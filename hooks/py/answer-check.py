#!/usr/bin/env python3
"""Stop gate: read the answer that was just given and refuse the easy failures.

natural-answering is a skill, which means it only applies when it is remembered.
This gate removes that condition: when a turn ends it pulls the last answer out of
the transcript and checks it. Findings block the turn **once**, so the answer gets
rewritten before the person reads it rather than after they complain.

Two things are checked that the prose checker cannot see on its own:

  repeated-question  the person asked again because the last answer missed.
                     Asking twice is the clearest evidence an answer missed —
                     stronger than anything measurable inside the answer itself.
                     Only messages a person typed count, and a new question that
                     merely shares a question word ("왜") is not asking again.
  answer-too-long    an answer past the one-screen limit the skill sets.

Blocking is capped by `stop_hook_active`, which Claude Code sets to true on the
retry after a Stop hook blocked. Seeing it means "already blocked once" — report
and let the turn end. No state file, and no way to loop.
"""

import difflib
import json
import os
import re
import subprocess
import sys
import tempfile

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKER = os.path.join(PLUGIN_ROOT, "skills", "natural-answering", "scripts", "check_prose.py")
REASK_MARKERS_FILE = os.path.join(PLUGIN_ROOT, "skills", "natural-answering", "data",
                                  "reask-markers.txt")
MAX_ANSWER_LINES = 30   # 스킬이 말하는 "화면 하나"에 여유를 둔 값
# 앞 질문과 이만큼 닮은 질문이 또 오면 같은 질문을 다시 보낸 것이다. difflib 닮은 정도(0~1).
# "어디에 저장돼?" -> "어디에 저장되는데?" 가 0.8 안팎이다. 바꾸려면 환경 변수로.
SAME_QUESTION_RATIO_ENV = "ANSWER_CHECK_SAME_QUESTION_RATIO"
DEFAULT_SAME_QUESTION_RATIO = 0.6
# 이보다 짧은 말("그래", "왜?")은 닮은 정도로 견주지 않는다. 짧은 말은 우연히 같기 쉽다.
MIN_CHARS_TO_COMPARE = 8


def typed_by_person(entry, content, text):
    """이 기록 줄이 사람이 직접 쓴 메시지인가.

    기록에서 역할이 user 인 줄에는 사람 글 말고도 기계가 넣은 글이 섞여 있다 — 규칙 묶음,
    대화 요약문, 훅 피드백, 도구 결과. 2026-11-11 에 이것들을 사람 메시지로 세서, 한 번만
    요청한 사람을 "같은 것을 다시 물었다" 고 막았다. 요즘 기록은 사람 글에 origin.kind 를
    "human" 으로 적어 둔다. 그 표시가 없는 옛 기록에서는 기계 글의 생김새로 뺀다.
    """
    origin = entry.get("origin")
    if isinstance(origin, dict):
        return origin.get("kind") == "human"
    if entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    if isinstance(content, list) and any(isinstance(block, dict) and block.get("type") == "tool_result"
                                         for block in content):
        return False
    # <system-reminder> 같은 태그로 시작하는 글도 기계가 넣은 것이다. 이 생김새 판단은 표시가
    # 없을 때만 쓴다 — 표시가 있으면, 사람이 붙여 넣은 "<div> ..." 도 사람 말이다.
    return not text.lstrip().startswith("<")


def read_turns(transcript_path):
    """대화 기록에서 (역할, 글) 목록을 순서대로. 도구 호출 블록은 글이 아니라 뺀다.

    역할은 "user"(사람이 쓴 글), "machine"(user 자리에 기계가 넣은 글), "assistant" 셋이다.
    """
    turns = []
    try:
        # 기록은 한 줄에 한 사건인 JSONL 이다. 중간에 깨진 줄이 있어도 나머지는 읽는다.
        with open(transcript_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                # 줄이 JSON 이어도 객체가 아닐 수 있다(null, 목록). 그런 줄은 사건이 아니라 건너뛴다.
                if not isinstance(entry, dict) or not isinstance(entry.get("message"), dict):
                    continue
                message = entry["message"]
                role = message.get("role")
                if role not in ("user", "assistant"):
                    continue
                # 내용은 문자열이거나 블록 목록이다. 블록 중 글(text)만 모으는 이유는,
                # 도구 호출·결과까지 합치면 답변이 아니라 작업 기록을 검사하게 되기 때문이다.
                content = message.get("content")
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = "\n".join(block.get("text", "") for block in content
                                     if isinstance(block, dict) and block.get("type") == "text")
                else:
                    text = ""
                if role == "user" and not typed_by_person(entry, content, text):
                    role = "machine"
                if text.strip():
                    turns.append((role, text))
    except OSError:
        return []
    return turns


def load_reask_markers():
    """되묻는 말투 목록을 읽는다. 파일이 없으면 빈 목록 — 말투 근거 없이 닮은 정도만 본다."""
    try:
        with open(REASK_MARKERS_FILE, encoding="utf-8") as handle:
            lines = [line.rstrip("\n") for line in handle]
    except OSError:
        return []
    return [re.compile(line) for line in lines if line.strip() and not line.startswith("#")]


def same_question_ratio():
    """같은 질문으로 볼 닮은 정도. 환경 변수가 0~1 숫자가 아니면 기본값을 쓴다."""
    try:
        ratio = float(os.environ.get(SAME_QUESTION_RATIO_ENV, DEFAULT_SAME_QUESTION_RATIO))
    except ValueError:
        return DEFAULT_SAME_QUESTION_RATIO
    return ratio if 0 < ratio <= 1 else DEFAULT_SAME_QUESTION_RATIO


def asked_again_because(previous, current, markers):
    """current 가 previous 를 다시 요청한 것이면 그 근거를, 새 요청이면 None 을 돌려준다.

    한 번만 요청한 것과 잘못 답해서 다시 요청한 것을 가르는 자리다. 근거는 둘 중 하나다.
      1. 되묻는 말투 ("모르겠다니까", "아니.... 내 질문") — 새 질문에는 잘 안 나온다
      2. 앞 질문과 거의 같은 질문을 또 보냄 — 말투 없이 같은 걸 다시 묻는 경우
    의문사가 겹치는 것만으로는 근거가 되지 않는다. "왜 고쳐야 해?" 다음의 "테스트는 왜
    따로 둬?" 는 새 질문이다.
    """
    for marker in markers:
        found = marker.search(current)
        if found:
            return "되묻는 말 '%s'" % found.group(0).strip()
    # 같은 "질문" 을 다시 보낸 것만 센다. 질문이 아닌 같은 말("다시 시작했어.", "그래")이나,
    # 지시 뒤의 확인 질문("항상 작동이 되어야지" -> "되게 했니?")은 다시 요청한 것이 아니다.
    if "?" not in current or "?" not in previous:
        return None
    if min(len(previous.strip()), len(current.strip())) < MIN_CHARS_TO_COMPARE:
        return None
    likeness = difflib.SequenceMatcher(None, previous.strip(), current.strip()).ratio()
    if likeness >= same_question_ratio():
        return "앞 질문과 거의 같은 질문 (닮은 정도 %.2f)" % likeness
    return None


def repeated_question(turns):
    """사람이 같은 것을 다시 요청했는가. (몇 번째인지, 근거) 를, 아니면 None 을 돌려준다.

    마지막 사람 메시지부터 거꾸로, 바로 앞 메시지를 다시 요청한 것인 동안 센다.
    처음 요청이 1번째이므로, 한 번 되물으면 2번째다.

    두 메시지 사이에 답이 있어야 한다. 답을 받기 전에 또 보낸 메시지(재전송, 대기열)는
    "답이 틀려서 다시 물은 것" 이 아니다 — 2026-11-11 기록에 6초 간격으로 같은 메시지가
    두 번 들어와 있었다.
    """
    # 사람 메시지마다 "그 앞에 답이 있었나" 를 같이 적는다. 기계 글은 둘 다에 끼지 않는다.
    messages, answered_before = [], []
    saw_answer = False
    for role, text in turns:
        if role == "assistant":
            saw_answer = True
        elif role == "user":
            messages.append(text)
            answered_before.append(saw_answer)
            saw_answer = False
    markers = load_reask_markers()
    times_asked, latest_reason = 1, None
    # 연달아 되물은 만큼만 센다. 중간에 새 요청이 하나라도 끼면 거기서 멈춘다.
    for index in range(len(messages) - 1, 0, -1):
        if not answered_before[index]:
            break
        reason = asked_again_because(messages[index - 1], messages[index], markers)
        if not reason:
            break
        times_asked += 1
        latest_reason = latest_reason or reason
    return (times_asked, latest_reason) if latest_reason else None


def check_answer(answer_text):
    """답변 글을 natural-answering 검사기에 넘긴다. 경고 줄만 돌려준다."""
    if not os.path.isfile(CHECKER):
        return ""
    # 검사기는 파일을 받는다. 답변은 파일이 아니므로 임시 파일로 한 번 내려 쓴다.
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                     encoding="utf-8") as answer_file:
        answer_file.write(answer_text)
        temp_path = answer_file.name
    try:
        finished = subprocess.run(
            [sys.executable, CHECKER, "--exit-zero", "--limit", "5", temp_path],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30)
        report = (finished.stdout or b"").decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        report = ""
    finally:
        os.unlink(temp_path)
    # 마지막 줄은 집계다. 그 줄만 있으면 경고가 없다.
    return report if len(report.splitlines()) > 1 else ""


def main():
    """답변을 검사하고, 처음 한 번만 막는다. 늘 0으로 끝난다(막는 것은 stdout 으로 알린다)."""
    raw_payload = sys.stdin.read()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0
    # Claude Code 는 늘 객체와 문자열 경로를 넘기지만, 모양이 틀린 입력에도 세션을 깨지 않는다.
    if not isinstance(event, dict) or not isinstance(event.get("transcript_path"), str):
        return 0

    turns = read_turns(event["transcript_path"])
    if not turns:
        return 0
    answers = [text for role, text in turns if role == "assistant"]
    if not answers:
        return 0
    answer_text = answers[-1]

    problems = []
    asked_again = repeated_question(turns)
    if asked_again:
        times_asked, reason = asked_again
        problems.append(
            "사용자가 같은 것을 다시 물었다 — 이번이 %d번째다 (근거: %s).\n"
            "   앞 답이 질문에 닿지 않았다는 뜻이다. 앞 답에 설명을 더 붙이지 말고,\n"
            "   질문의 낱말을 그대로 쓴 한 문장으로 먼저 답한 뒤 설명은 그 뒤에 둔다."
            % (times_asked, reason))

    line_count = len([line for line in answer_text.splitlines() if line.strip()])
    if line_count > MAX_ANSWER_LINES:
        problems.append(
            "답변이 %d줄이다(기준 %d줄). 화면 하나를 넘으면 답변이 아니라 문서다.\n"
            "   요약 세 줄과 경로를 주거나, 지금 묻지 않은 부분을 덜어낸다"
            % (line_count, MAX_ANSWER_LINES))

    prose_report = check_answer(answer_text)
    if prose_report:
        problems.append("글 검사가 잡은 것:\n" + prose_report)

    if not problems:
        return 0

    listed = "\n\n".join("%d. %s" % (number, text)
                         for number, text in enumerate(problems, 1))
    # 이미 한 번 막았으면 다시 막지 않는다. 고칠 기회는 한 번이면 되고, 두 번이면 반복이 된다.
    if event.get("stop_hook_active"):
        print("natural-answering: 남은 지적 (막지 않음)\n" + listed)
        return 0
    # ensure_ascii=False: 막는 이유를 사람과 모델이 다 읽는다. \uXXXX 로 쓰면 둘 다 못 읽는다.
    print(json.dumps({"decision": "block", "reason":
        "natural-answering: 답변을 고치고 다시 끝낼 것.\n\n" + listed},
        ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
