**English** · [한국어](task-checklist-ko.md) · [日本語](task-checklist-ja.md) · [中文](task-checklist-zh.md) · [Español](task-checklist-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# task-checklist

Turns every instruction into a checklist before working, and finishes only when every item is done or closed with a reason.

## Use it in Claude

Nothing to say: the `checklist-start` gate asks for a checklist on every message.

## What it does

1. Read the whole message: numbered items, requests buried in sentences, decisions you already made.
2. Split it into items that can be checked — "tests pass" rather than "improve the tests". A question in the message is an item too.
3. Write them to the session's checklist, one per line: `- [ ] item`.
4. Mark each item `- [x]` as soon as it is done; close one that cannot be done as `- [~] item — reason`.
5. Before ending, open the list again and finish whatever is still `- [ ]`.

## Files and scripts

```text
~/.claude/checklists/<session>.md        this instruction's list
~/.claude/checklists/<session>.prev.md   the previous instruction's list, kept
```

`KL_CHECKLIST_DIR` moves the folder.

## Hooks that back it

`checklist-start` moves the previous list aside and says where to write the new one. `checklist-check` sends the answer back once if the list is missing or has open items.

## Limits

The gate sees whether items are marked, not whether the work behind the mark was done well.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
