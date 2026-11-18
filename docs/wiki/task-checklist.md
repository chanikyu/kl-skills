**English** · [한국어](task-checklist-ko.md) · [日本語](task-checklist-ja.md) · [中文](task-checklist-zh.md) · [Español](task-checklist-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# task-checklist

Turns every instruction into a checklist before working, and finishes only when every item is done or closed with a reason.

## Use it in Claude

Nothing to say: the `checklist-start` gate asks for a checklist on every message.

## What it does

1. Read the whole message: numbered items, requests buried in sentences, decisions you already made. If it can be read two ways, do not pick one and start: write `- [ ] question: A or B` as the first item and ask.
2. Split it into items that can be checked — "tests pass" rather than "improve the tests". End each item with `→ check: …`, saying what will show it is done. A question in the message is an item too.
3. Write them to the session's checklist, one per line: `- [ ] item`.
4. Mark each item `- [x]` as soon as it is done; close one that cannot be done as `- [~] item — reason`.
5. Before ending, open the list again and finish whatever is still `- [ ]`.

## Files and scripts

```text
~/.claude/checklists/<session>.md         this instruction's list, open items carried over on top
~/.claude/checklists/<session>.prev.md    the previous instruction's whole list, kept
~/.claude/checklists/<session>.carry.md   the open items that were carried over
```

`KL_CHECKLIST_DIR` moves the folder.

## Hooks that back it

`checklist-start` keeps the previous list as `.prev.md`, carries its open items to the top of the new list, and says where to add the new items. `checklist-check` sends the answer back once if the list is missing, has open items, or lost a carried item without closing it.

## Limits

The gate sees whether items are marked, not whether the work behind the mark was done well.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
