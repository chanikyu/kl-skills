#!/usr/bin/env python3
"""Stop gate: read the answer that was just given and refuse the easy failures.

natural-answering is a skill, which means it only applies when it is remembered.
This gate removes that condition: when a turn ends it pulls the last answer out of
the transcript and checks it. Findings block the turn **once**, so the answer gets
rewritten before the person reads it rather than after they complain.

Two things are checked that the prose checker cannot see on its own:

  repeated-question  the same question word came back in the next user message.
                     Asking twice is the clearest evidence an answer missed —
                     stronger than anything measurable inside the answer itself.
  answer-too-long    an answer past the one-screen limit the skill sets.

Blocking is capped by `stop_hook_active`, which Claude Code sets to true on the
retry after a Stop hook blocked. Seeing it means "already blocked once" — report
and let the turn end. No state file, and no way to loop.
"""

import json
import os
import subprocess
import sys
import tempfile

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKER = os.path.join(PLUGIN_ROOT, "skills", "natural-answering", "scripts", "check_prose.py")
MAX_ANSWER_LINES = 30   # 스킬이 말하는 "화면 하나"에 여유를 둔 값
# 질문을 가리키는 말. 연속한 두 사용자 메시지에 같은 것이 들어 있으면 답이 닿지 않은 것이다.
QUESTION_WORDS = ("왜", "어떻게", "무엇", "뭐", "뭔", "무슨", "언제", "어디", "누가", "얼마",
                  "되는거", "되는 거", "why", "how", "what", "when", "where")


def read_turns(transcript_path):
    """대화 기록에서 (역할, 글) 목록을 순서대로. 도구 호출 블록은 글이 아니라 뺀다."""
    turns = []
    try:
        # 기록은 한 줄에 한 사건인 JSONL 이다. 중간에 깨진 줄이 있어도 나머지는 읽는다.
        with open(transcript_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                message = entry.get("message") or {}
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
                if text.strip():
                    turns.append((role, text))
    except OSError:
        return []
    return turns


def repeated_question(turns):
    """사용자가 같은 질문을 다시 했는가. 그 말을 돌려준다."""
    questions = [text for role, text in turns if role == "user"][-2:]
    if len(questions) < 2:
        return None
    previous, current = questions
    # 두 메시지에 같은 의문사가 들어 있고, 뒤쪽이 물음표나 반복 부호로 끝나면 되묻는 것이다.
    for word in QUESTION_WORDS:
        if word in previous and word in current:
            if "?" in current or "???" in current or current.strip().endswith(("나", "냐", "야")):
                return word
    return None


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

    turns = read_turns(event.get("transcript_path", ""))
    if not turns:
        return 0
    answers = [text for role, text in turns if role == "assistant"]
    if not answers:
        return 0
    answer_text = answers[-1]

    problems = []
    asked_again = repeated_question(turns)
    if asked_again:
        problems.append(
            "사용자가 '%s' 를 다시 물었다. 앞 답이 질문에 닿지 않았다는 뜻이다.\n"
            "   질문의 낱말을 그대로 쓴 한 문장으로 먼저 답하고, 설명은 그 뒤에 둔다." % asked_again)

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
