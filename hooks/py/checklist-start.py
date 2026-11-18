#!/usr/bin/env python3
"""UserPromptSubmit gate: every instruction starts its checklist — open items carry over.

The previous turn's checklist is kept whole as <session>.prev.md. Its open items do
not go away with it: they are written at the top of the new list (one heading per
original instruction) and recorded in <session>.carry.md, so the Stop gate keeps
asking for them until each is done or closed with a reason. The model is told
which items came over and where to add this instruction's items. The method is
the task-checklist skill.

Asked for on 2026-11-13: "analyse the instruction, make a checklist, work, then
check every item is done; finish what is not". Carry-over asked for on 2026-11-18:
a side question in the middle of a task moved the task's list aside, and its open
items were never looked at again.
"""

import json
import os
import sys

from _checklist import (CARRIED_HEADING, OPEN_ITEM, carry_path, checklist_path, item_name, item_names,
                        open_items_by_heading, read_text)
from _hook_output import is_machine_prompt, read_payload, tell_model

MAX_CARRIED_SHOWN = 5   # 메시지에 보여 줄 넘어온 항목 수. 더 많으면 개수만 덧붙인다


def carry_over(path):
    """지난 목록은 .prev 로 보관하고, 안 끝난 항목은 새 목록 맨 위로 넘긴다. 넘긴 항목 글 목록을 돌려준다."""
    text = read_text(path)
    carried = open_items_by_heading(text) if text is not None else []
    # 지난번에 넘어왔는데 닫지 않고 목록에서 지운 항목도 다시 넘긴다 — 지우는 것은 끝내는 것이 아니다
    names_now = item_names(text)
    lost = [("목록에서 지워졌던 항목", item) for item in OPEN_ITEM.findall(read_text(carry_path(path)) or "")
            if item and item_name(item) not in names_now]
    carried = lost + carried
    if text is not None:
        os.replace(path, path[:-3] + ".prev.md")
    if not carried:
        if os.path.exists(carry_path(path)):
            os.remove(carry_path(path))
        return []
    blocks, heading_now = [], None
    for heading, item in carried:
        if heading != heading_now:
            blocks.append("%s## %s%s\n" % ("\n" if blocks else "", CARRIED_HEADING, heading))
            heading_now = heading
        blocks.append("- [ ] %s\n" % item)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(blocks) + "\n")
    with open(carry_path(path), "w", encoding="utf-8") as handle:
        handle.write("".join("- [ ] %s\n" % item for _, item in carried))
    return [item for _, item in carried]


def carried_notice(path, carried):
    """넘어온 항목을 알리는 앞머리. 넘어온 것이 없으면 빈 글."""
    if not carried:
        return ""
    shown = "\n".join("    - [ ] " + item for item in carried[:MAX_CARRIED_SHOWN])
    more = "\n    … 그리고 %d개 더" % (len(carried) - MAX_CARRIED_SHOWN) if len(carried) > MAX_CARRIED_SHOWN else ""
    return ("checklist: 지난 지시에서 넘어온 안 끝난 항목 %d개를 이 목록 맨 위에 적어 두었다 → %s\n%s%s\n"
            "  파일을 덮어쓰지 말고 그 아래에 이번 지시의 항목을 덧붙인다."
            " 넘어온 항목은 이름을 고치지 말고 칸만 바꾼다(마저 하거나 '- [~] 항목 — 이유').\n"
            % (len(carried), path, shown, more))


def main():
    """지난 목록의 안 끝난 항목을 넘기고, 이번 지시의 체크리스트를 어디에 어떻게 쓸지 알린다. 늘 0으로 끝난다."""
    raw_payload = read_payload()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0
    if not isinstance(event, dict) or not str(event.get("prompt") or "").strip():
        return 0
    # 작업 끝 알림처럼 기계가 보낸 글은 새 지시가 아니다. 목록을 치우면 하던 일의 목록이 사라진다.
    if is_machine_prompt(str(event["prompt"])):
        return 0
    path = checklist_path(event.get("session_id"))
    if not path:
        return 0
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # 지난 지시의 목록은 통째로 보관한다. 지우면 무엇이 남았었는지 되짚을 수 없다.
        carried = carry_over(path)
    except OSError:
        return 0
    tell_model("UserPromptSubmit",
               carried_notice(path, carried) +
               "checklist: 이 지시를 항목으로 나눠 체크리스트를 먼저 쓴다 → %s\n"
               "  한 줄에 '- [ ] 항목'. 끝낸 것은 '- [x]', 할 수 없는 것은 '- [~] 항목 — 이유'.\n"
               "  뜻이 둘로 읽히면 첫 항목에 '- [ ] 질문: A인가 B인가' 를 쓰고 먼저 묻는다."
               " 항목마다 '→ 확인: …' 을 붙인다.\n"
               "  답을 끝내기 전에 남은 '- [ ]' 가 없는지 대조한다 (방법: kl-skills:task-checklist 스킬)."
               % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
