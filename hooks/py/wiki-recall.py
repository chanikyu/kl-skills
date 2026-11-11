#!/usr/bin/env python3
"""UserPromptSubmit gate: 사용자가 말할 때마다 위키에서 관련 페이지를 찾아 붙인다.

위키는 한 번 정리한 지식을 다시 쓰려고 만든 것인데, 찾아 읽지 않으면 없는 것과 같다. 이전
세션에서 이미 결론을 낸 주제를 처음부터 다시 조사하는 일이 그렇게 생긴다. 이 훅은 메시지가
들어올 때마다 위키를 검색해서, 관련이 분명한 페이지의 경로와 핵심 줄을 모델에게 넘긴다.

가볍게 붙인다. 페이지 전체가 아니라 경로·제목·몇 줄이다. 매 메시지마다 붙으므로, 길면 대화를
잠식한다. 깊게 읽을 때는 wiki-recall 스킬이 위키 크기에 따라 통째로(CAG) 또는 골라서(RAG)
본문을 가져온다.

관련이 약하면 아무것도 붙이지 않는다. 엉뚱한 페이지가 매번 붙으면 이 훅은 잡음이 되고 꺼진다.
기준은 둘이다: 질문의 낱말을 두 개 이상 가진 페이지이면서, 드문 낱말에 무게를 둔 '질문을 덮는
비율' 이 40% 이상일 것. 2026-11-11 실제 위키에서 관련 질문은 52~69%, 무관한 질문은 18% 였다.
"""

import json
import os
import subprocess
import sys

from _hook_output import tell_model

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECALL = os.path.join(PLUGIN_ROOT, "skills", "wiki-recall", "scripts", "recall.py")
MIN_PROMPT_CHARS = 8        # "그래", "확인해줘" 같은 짧은 말로는 찾을 것이 없다
# 덮는 비율 기준. 환경변수로 바꿀 수 있다 — 위키가 커지면 맞는 값이 달라질 수 있어서다.
MIN_COVERAGE = os.environ.get("WIKI_RECALL_MIN_COVERAGE", "0.4")


def main():
    """메시지를 받아 위키를 찾고, 관련이 분명할 때만 넘긴다. 늘 0으로 끝난다."""
    raw_payload = sys.stdin.read()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0
    prompt = (event.get("prompt") or "").strip()
    # 짧은 말과 / 로 시작하는 명령은 검색할 내용이 아니다.
    if len(prompt) < MIN_PROMPT_CHARS or prompt.startswith("/") or not os.path.isfile(RECALL):
        return 0

    try:
        finished = subprocess.run(
            [sys.executable, RECALL, "--mode", "rag", "--top", "3",
             "--min-shared", "2", "--min-coverage", MIN_COVERAGE],
            input=prompt.encode("utf-8"), stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return 0

    found = (finished.stdout or b"").decode("utf-8", "replace").strip()
    if finished.returncode != 0 or not found:
        return 0
    tell_model("UserPromptSubmit",
               found + "\n(wiki-recall: 위키에 이미 정리된 내용이 있다. 여기 줄은 검색으로 고른 "
                       "일부라서, 인용하려면 페이지를 열어 확인해야 정확하다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
