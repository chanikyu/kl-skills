#!/usr/bin/env python3
"""Stop gate: the answer may end only when every item on the checklist is closed.

Reads the session's checklist, which also holds the open items carried over from
earlier instructions (checklist-start). Blocks the turn once if there is no
checklist, if items are still open ('- [ ]'), or if a carried item has vanished
from the list without being closed: the model gets them back and finishes them
before the answer reaches the person. Blocking is capped by stop_hook_active, so
the retry always ends — whatever is still open is then reported, not blocked again.
"""

import json
import sys

from _checklist import OPEN_ITEM, carry_path, checklist_path, item_name, item_names, read_items, read_text
from _hook_output import read_payload

MAX_ITEMS_SHOWN = 10   # 돌려보낼 때 보여 줄 미완료 항목 수. 더 많으면 개수만 덧붙인다


def lost_carried(path):
    """지난 지시에서 넘어왔는데 지금 목록에 없는 항목. 닫지 않고 지웠거나, 목록을 덮어쓴 것이다."""
    carried = OPEN_ITEM.findall(read_text(carry_path(path)) or "")
    names = item_names(read_text(path))
    return [item for item in carried if item and item_name(item) not in names]


def listed(items):
    """돌려보낼 항목 줄. 많으면 앞의 몇 개와 남은 개수만."""
    shown = "\n".join("   - [ ] " + (item or "(내용 없는 칸)") for item in items[:MAX_ITEMS_SHOWN])
    more = "\n   … 그리고 %d개 더" % (len(items) - MAX_ITEMS_SHOWN) if len(items) > MAX_ITEMS_SHOWN else ""
    return shown + more


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
    lost = lost_carried(path)
    if total and not open_items and not lost:
        return 0
    reasons = []
    if not total:
        reasons.append("checklist: 이번 지시의 체크리스트가 없다 (%s).\n"
                       "   지시를 항목으로 나눠 쓰고, 한 일과 하나씩 대조한 뒤 끝낸다." % path)
    elif open_items:
        reasons.append("checklist: 안 끝난 항목이 %d개 남았다 (%s).\n%s\n"
                       "   마저 하고 '- [x]' 로 바꾼 뒤 끝낸다. 할 수 없는 항목은 '- [~] 항목 — 이유' 로 바꾸고 답에 밝힌다."
                       % (len(open_items), path, listed(open_items)))
    if lost:
        reasons.append("checklist: 지난 지시에서 넘어온 항목 %d개가 닫히지 않은 채 목록에서 사라졌다.\n%s\n"
                       "   목록에 되살려 마저 하거나 '- [~] 항목 — 이유' 로 닫는다. 지우는 것은 끝내는 것이 아니다."
                       % (len(lost), listed(lost)))
    reason = "\n".join(reasons)
    # 이미 한 번 돌려보냈으면 다시 막지 않는다. 남은 것은 알리기만 한다 — 반복은 세션을 멈춘다.
    if event.get("stop_hook_active"):
        print(reason.replace("checklist:", "checklist (막지 않음):", 1))
        return 0
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
