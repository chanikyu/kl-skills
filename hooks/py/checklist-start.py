#!/usr/bin/env python3
"""UserPromptSubmit gate: every instruction starts a fresh checklist.

The previous turn's checklist is moved aside (<session>.prev.md), so the Stop gate
only ever reads the list made for this instruction — a leftover open item from an
earlier turn must not block this one. Then the model is told where to write the
new list and how to mark it. The method is the task-checklist skill.

Asked for on 2026-11-13: "analyse the instruction, make a checklist, work, then
check every item is done; finish what is not". Applies to every instruction.
"""

import json
import os
import sys

from _checklist import checklist_path
from _hook_output import read_payload, tell_model


def main():
    """이전 체크리스트를 치우고, 이번 지시의 체크리스트를 어디에 어떻게 쓸지 알린다. 늘 0으로 끝난다."""
    raw_payload = read_payload()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0
    if not isinstance(event, dict) or not str(event.get("prompt") or "").strip():
        return 0
    path = checklist_path(event.get("session_id"))
    if not path:
        return 0
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # 지난 지시의 목록은 보관만 한다. 지우면 무엇이 남았었는지 되짚을 수 없다.
        if os.path.exists(path):
            os.replace(path, path[:-3] + ".prev.md")
    except OSError:
        return 0
    tell_model("UserPromptSubmit",
               "checklist: 이 지시를 항목으로 나눠 체크리스트를 먼저 쓴다 → %s\n"
               "  한 줄에 '- [ ] 항목'. 끝낸 것은 '- [x]', 할 수 없는 것은 '- [~] 항목 — 이유'.\n"
               "  답을 끝내기 전에 남은 '- [ ]' 가 없는지 대조한다 (방법: kl-skills:task-checklist 스킬)."
               % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
