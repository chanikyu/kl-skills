#!/usr/bin/env python3
"""Stop gate: the answer may end only when this instruction's checklist is done.

Reads the session's checklist (written after checklist-start moved the old one
aside). Blocks the turn once if there is no checklist, or if items are still
open ('- [ ]'): the model gets the open items back and finishes them before the
answer reaches the person. Blocking is capped by stop_hook_active, so the retry
always ends — whatever is still open is then reported, not blocked again.
"""

import json
import sys

from _checklist import checklist_path, read_items
from _hook_output import read_payload

MAX_ITEMS_SHOWN = 10   # 돌려보낼 때 보여 줄 미완료 항목 수. 더 많으면 개수만 덧붙인다


def main():
    """체크리스트를 읽고, 없거나 안 끝난 항목이 있으면 한 번 막는다. 늘 0으로 끝난다."""
    raw_payload = read_payload()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0
    if not isinstance(event, dict):
        return 0
    path = checklist_path(event.get("session_id"))
    if not path:
        return 0
    open_items, total = read_items(path)
    if total and not open_items:
        return 0
    if not total:
        reason = ("checklist: 이번 지시의 체크리스트가 없다 (%s).\n"
                  "   지시를 항목으로 나눠 쓰고, 한 일과 하나씩 대조한 뒤 끝낸다." % path)
    else:
        shown = "\n".join("   - [ ] " + (item or "(내용 없는 칸)") for item in open_items[:MAX_ITEMS_SHOWN])
        more = "\n   … 그리고 %d개 더" % (len(open_items) - MAX_ITEMS_SHOWN) if len(open_items) > MAX_ITEMS_SHOWN else ""
        reason = ("checklist: 안 끝난 항목이 %d개 남았다 (%s).\n%s%s\n"
                  "   마저 하고 '- [x]' 로 바꾼 뒤 끝낸다. 할 수 없는 항목은 '- [~] 항목 — 이유' 로 바꾸고 답에 밝힌다."
                  % (len(open_items), path, shown, more))
    # 이미 한 번 돌려보냈으면 다시 막지 않는다. 남은 것은 알리기만 한다 — 반복은 세션을 멈춘다.
    if event.get("stop_hook_active"):
        print(reason.replace("checklist:", "checklist (막지 않음):", 1))
        return 0
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
