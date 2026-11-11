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
  work-report        a turn that changed the user's files (or committed) must end
                     with the six-step work report, in order, read from the table
                     in references/work-report.md.

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

# 사람 메시지와 기계 글을 가르는 규칙은 hook-replay 스킬과 같이 쓴다.
from _transcript import read_turns, tool_calls_since_last_human
from _work_files import is_work_file

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKER = os.path.join(PLUGIN_ROOT, "skills", "natural-answering", "scripts", "check_prose.py")
REASK_MARKERS_FILE = os.path.join(PLUGIN_ROOT, "skills", "natural-answering", "data",
                                  "reask-markers.txt")
WORK_REPORT_GUIDE = os.path.join(PLUGIN_ROOT, "skills", "natural-answering", "references",
                                 "work-report.md")
# Claude Code 가 파일을 쓰는 도구와, 그 입력에서 경로가 든 칸 — 외부 규격이다.
EDIT_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path"}
# 명령 첫머리의 git ... commit. 줄 머리나 ; & | ( { 뒤에서 시작하고, 사이에는 환경 변수 지정과
# git 의 전역 옵션(-C 경로, -c 키=값, --git-dir 경로 같은 값 있는 옵션, --옵션)만 올 수 있다.
# 줄 어디서나 두 낱말을 찾으면 패치 코드 속 문자열까지 커밋으로 셌다(2026-11-11 hook-replay).
COMMIT_COMMAND = re.compile(
    r"(?:^|[;&|({])\s*(?:\w+=\S+\s+)*git\s+"
    r"(?:(?:-[cC]|--(?:git-dir|work-tree|namespace|super-prefix|config-env))\s+\S+\s+|--\S+\s+)*"
    r"commit(?![\w-])", re.MULTILINE)
# 여러 줄 글(heredoc)의 본문과 따옴표 안은 명령이 아니라 글이다. 커밋을 찾기 전에 지운다.
HEREDOC_BODY = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n[ \t]*\2[ \t]*(?=\n|$)", re.DOTALL)
QUOTED_TEXT = re.compile(r"\"[^\"]*\"|'[^']*'")
GUIDE_TABLE_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$")
OUTCOME_LOOKAHEAD_CHARS = 80   # 1단계 이름 뒤에서 결과 낱말을 찾는 범위. 제목 다음 줄까지 닿는다
MAX_ANSWER_LINES = 30   # 스킬이 말하는 "화면 하나"에 여유를 둔 값
# 앞 질문과 이만큼 닮은 질문이 또 오면 같은 질문을 다시 보낸 것이다. difflib 닮은 정도(0~1).
# "어디에 저장돼?" -> "어디에 저장되는데?" 가 0.8 안팎이다. 바꾸려면 환경 변수로.
SAME_QUESTION_RATIO_ENV = "ANSWER_CHECK_SAME_QUESTION_RATIO"
DEFAULT_SAME_QUESTION_RATIO = 0.6
# 이보다 짧은 말("그래", "왜?")은 닮은 정도로 견주지 않는다. 짧은 말은 우연히 같기 쉽다.
MIN_CHARS_TO_COMPARE = 8


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


def work_report_steps():
    """작업 보고 단계 이름(순서대로)과 1단계의 결과 낱말. 정본인 work-report.md 의 표에서 읽는다.

    이름을 코드에 베끼면 문서를 고쳐도 검사는 옛 이름을 요구한다. 표가 하나뿐이라 첫 칸이
    숫자인 행을 순서대로 읽으면 된다.
    """
    steps, outcomes = [], []
    try:
        with open(WORK_REPORT_GUIDE, encoding="utf-8") as handle:
            for line in handle:
                row = GUIDE_TABLE_ROW.match(line.strip())
                if not row:
                    continue
                steps.append(row.group(2))
                # 1단계 칸은 "완료 / 부분 완료 / 실패 — 한 단어로 먼저" 꼴이다.
                if not outcomes:
                    outcomes = [word.strip() for word in row.group(3).split("—")[0].split("/")
                                if word.strip()]
    except OSError:
        return [], []
    return steps, outcomes


def runs_commit(command):
    """이 셸 명령이 git commit 을 돌리나. 글(heredoc 본문, 따옴표 안)은 명령이 아니다.

    리뷰가 재현한 네 가지(2026-11-11): heredoc 본문의 줄과 echo 'a; git commit' 를 커밋으로
    셌고, git --git-dir /x commit 과 (git commit) 은 놓쳤다. 따옴표는 지우되 빈 따옴표를 남겨,
    -C "/a b" 같은 옵션 자리는 그대로 둔다. 셸 해석기가 아니다 — 명령 자리만 찾으면 된다.
    """
    without_heredocs = HEREDOC_BODY.sub("\n", command)
    without_quoted = QUOTED_TEXT.sub(lambda quoted: quoted.group(0)[0] * 2, without_heredocs)
    return bool(COMMIT_COMMAND.search(without_quoted))


def turn_changed_work(tool_calls):
    """이번 턴에 사용자 파일을 고쳤거나 커밋했나. 위키 페이지·임시 폴더만 쓴 턴은 아니다.

    턴이 끝날 때 남아 있지 않은 파일은 세지 않는다. 훅 확인용으로 쓰고 바로 지운 파일 같은
    것이라, 보고할 변경이 남지 않았다.
    """
    for name, tool_input in tool_calls:
        path_key = EDIT_TOOLS.get(name)
        path = str(tool_input.get(path_key) or "") if path_key else ""
        # exists 를 먼저 본다. 경로가 이상하면(NUL 글자 등) exists 는 False 로 끝나지만,
        # is_work_file 안의 realpath 는 예외를 던진다.
        if path and os.path.exists(path) and is_work_file(path):
            return True
        if name == "Bash" and runs_commit(str(tool_input.get("command") or "")):
            return True
    return False


def work_report_gaps(answer_text, steps, outcomes):
    """작업 보고에서 빠진 것들. 단계가 빠졌나, 순서가 맞나, 1단계 뒤에 결과 낱말이 있나."""
    found = {}
    for step in steps:
        # 줄 머리의 단계 이름. 제목(##)·굵게(**)·번호(1.)가 앞에 붙어도 같은 단계다.
        label = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:\d+[.)]\s*)?(?:\*\*)?"
                           + re.escape(step) + r"(?![가-힣])", re.MULTILINE)
        match = label.search(answer_text)
        if match:
            found[step] = match
    gaps = []
    missing = [step for step in steps if step not in found]
    if missing:
        gaps.append("빠진 단계: " + ", ".join(missing))
    starts = [found[step].start() for step in steps if step in found]
    if starts != sorted(starts):
        gaps.append("순서가 다르다 — " + " → ".join(steps))
    first_step = steps[0] if steps else None
    if first_step in found:
        end = found[first_step].end()
        following = answer_text[end:end + OUTCOME_LOOKAHEAD_CHARS].lstrip(" \t\n:*#—–-")
        if not any(following.startswith(word) for word in outcomes):
            gaps.append("'%s' 바로 뒤에 %s 중 하나를 먼저 쓴다" % (first_step, " / ".join(outcomes)))
    return gaps


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

    # 코드를 고친 턴은 작업 보고로 끝낸다. 무엇이 됐고, 무엇을 바꿨고, 확인했고, 무엇이 남았나.
    if turn_changed_work(tool_calls_since_last_human(event["transcript_path"])):
        steps, outcomes = work_report_steps()
        gaps = work_report_gaps(answer_text, steps, outcomes) if steps else []
        if gaps:
            problems.append(
                "파일을 고친 턴이라 작업 보고 %d단계로 끝내야 한다(references/work-report.md).\n   "
                % len(steps) + "\n   ".join(gaps)
                + "\n   단계마다 한두 줄이면 된다 — 화면 하나 안에 담는다.")

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
