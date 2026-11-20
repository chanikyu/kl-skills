"""훅이 모델에게 무언가를 알리는 단 하나의 방법.

PostToolUse 와 Stop 훅이 그냥 글로 찍은 것은 Claude Code 의 디버그 기록에만 남고 모델에게는
전달되지 않는다(공식 문서, hooks 참고 문서의 "stdout" 항목). 모델에게 닿는 길은
`hookSpecificOutput.additionalContext` 라는 JSON 칸 하나다. 도구 결과 바로 옆에 붙어서 간다.

2026-11-11 까지 이 리포의 게이트들은 그냥 글로 찍고 있었다. 그래프를 다시 만드는 것처럼
결과물을 남기는 일은 됐지만, 글 검사·코드 검사의 지적은 한 번도 모델에게 닿지 않았다.
그 모양을 여기 한 곳에 둔다 — 게이트마다 따로 쓰면 하나만 고쳐지고 나머지는 또 조용해진다.

이 파일 이름이 밑줄로 시작하는 것은 run.sh 가 이걸 게이트로 착각하지 않게 하기 위해서다.
"""

import json
import os
import re
import sys

# 코덱스는 파일을 고칠 때 경로 대신 패치 글을 넘긴다: tool_name 이 "apply_patch", tool_input 이
# {"command": "*** Begin Patch\n*** Update File: a.py\n..."} 다. 파일마다 머리 줄이 하나씩이고 경로는
# 작업 폴더 기준이다(openai/codex codex-rs/core/src/tools/handlers/apply_patch.rs, 2026-11-20 확인).
# 지운 파일(Delete File)은 검사할 글이 없어서 뺀다.
PATCH_FILE_LINE = re.compile(r"^\*\*\* (?:Add File|Update File|Move to): (.+?)\s*$", re.MULTILINE)
# 사람이 쓴 지시가 아닌데 UserPromptSubmit 로 들어오는 글(작업 끝 알림 등)의 첫머리 목록
MACHINE_PROMPT_STARTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "data", "machine-prompt-starts.txt")


def read_payload():
    """훅 입력(stdin)을 글로 읽는다. UTF-8 이 아닌 바이트가 와도 터지지 않고 대체 글자로 읽는다.

    sys.stdin.read() 는 깨진 바이트에서 UnicodeDecodeError 로 죽는다(2026-11-13 리뷰가 재현).
    게이트가 죽으면 그 이벤트가 걸린 세션 전체가 흔들리므로, 읽기에서부터 막는다.
    """
    return sys.stdin.buffer.read().decode("utf-8", "replace")


def edited_paths(event):
    """도구가 쓴 파일 경로 목록. Claude Code 는 tool_input.file_path 하나, 코덱스는 패치 글의 파일 줄들이다."""
    tool_input = event.get("tool_input") if isinstance(event, dict) else None
    if not isinstance(tool_input, dict):
        return []
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if isinstance(path, str) and path:
        return [path]
    patch = tool_input.get("command")
    if event.get("tool_name") != "apply_patch" or not isinstance(patch, str):
        return []
    cwd = event.get("cwd") if isinstance(event.get("cwd"), str) else ""
    return [os.path.normpath(os.path.join(cwd, found)) for found in PATCH_FILE_LINE.findall(patch)]


def report_quietly(text):
    """막지 않는 알림을 Stop 훅에서 남긴다. 표준 오류로 보낸다.

    코덱스는 Stop 훅이 0으로 끝나며 JSON 이 아닌 글을 찍으면 매번 '잘못된 출력' 오류로 띄운다
    (openai/codex codex-rs/hooks/src/events/stop.rs). Claude Code 도 Stop 의 그냥 글은 자세히 보기에만
    남겨 모델에게 닿지 않으므로, 표준 오류로 옮겨도 모델이 받는 것은 그대로다.
    """
    sys.stderr.write(text.rstrip("\n") + "\n")


def is_machine_prompt(prompt):
    """사람이 아니라 기계가 보낸 글인가(작업 끝 알림 같은 것). 첫머리 목록은 데이터 파일에 있다.

    메시지를 받는 게이트(wiki-recall, skill-match, checklist-start)가 모두 이것으로 거른다.
    2026-11-13: 작업 끝 알림을 사람 메시지로 알고 체크리스트를 치우고, 알림 글로 스킬·위키를 찾았다.
    """
    try:
        with open(MACHINE_PROMPT_STARTS, encoding="utf-8") as handle:
            starts = [line.rstrip("\n") for line in handle if line.strip() and not line.startswith("#")]
    except OSError:
        return False
    head = prompt.lstrip()
    return any(head.startswith(start) for start in starts)


def tell_model(event_name, text):
    """text 를 모델에게 넘긴다. 출력은 이 JSON 한 덩어리뿐이어야 한다.

    앞뒤에 다른 글이 섞이면 Claude Code 가 JSON 으로 읽지 못하고 통째로 버린다.
    한글을 그대로 두는 것(ensure_ascii=False)은 기록을 열어 보는 사람도 읽게 하기 위해서다.
    """
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event_name,
                                             "additionalContext": text}},
                     ensure_ascii=False))
