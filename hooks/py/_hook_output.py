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
import sys

# 사람이 쓴 지시가 아닌데 UserPromptSubmit 로 들어오는 글(작업 끝 알림 등)의 첫머리 목록
MACHINE_PROMPT_STARTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "data", "machine-prompt-starts.txt")


def read_payload():
    """훅 입력(stdin)을 글로 읽는다. UTF-8 이 아닌 바이트가 와도 터지지 않고 대체 글자로 읽는다.

    sys.stdin.read() 는 깨진 바이트에서 UnicodeDecodeError 로 죽는다(2026-11-13 리뷰가 재현).
    게이트가 죽으면 그 이벤트가 걸린 세션 전체가 흔들리므로, 읽기에서부터 막는다.
    """
    return sys.stdin.buffer.read().decode("utf-8", "replace")


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
