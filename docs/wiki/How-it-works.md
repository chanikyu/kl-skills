**English** · [한국어](How-it-works-ko.md) · [日本語](How-it-works-ja.md) · [中文](How-it-works-zh.md) · [Español](How-it-works-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# How it works

<img src="../../assets/turn-flow.png" alt="One turn: the session starts, a message comes in, files are written, Bash runs, the answer ends. Each moment runs its hook gates." width="100%" />

## Skills, hook gates and the wiki

<img src="../../assets/parts.png" alt="Your message goes to Claude Code, which reads skills, is checked by hook gates and keeps what it learns in the wiki." width="100%" />

- **Skills** say how a job is done. Claude Code loads a skill when the conversation matches its
  description. That match is the model's own call, so it is not guaranteed.
- **Hook gates** run at fixed moments whether or not anyone remembers them. `skill-match` closes the
  gap above: it matches every message against each skill's trigger words and names the skill that fits.
  The trigger words are English and Korean; in other languages Claude still matches the description itself.
- **The wiki** keeps what was learned, one page per topic, and `wiki-recall` brings it back.

## Hook gates

| When | Gate | What it does | Sends the answer back |
| --- | --- | --- | --- |
| Session starts | `session-start` | Prints the banner | — |
| A message comes in | `wiki-recall` | Attaches related wiki pages | — |
| A message comes in | `skill-match` | Names the skill this message is for | — |
| A message comes in | `checklist-start` | Says where to write this instruction's checklist | — |
| A file is written | `wiki-index-check` | Flags a wiki page missing from the index | — |
| A file is written | `wiki-graph` | Redraws the wiki graph | — |
| A file is written | `prose-check` | Flags hard-to-read spots in wiki pages | — |
| A file is written | `code-check` | Flags vague Python names and missing docstrings | — |
| A file is written | `plan-drift` | Checks a plan's frame and drift | — |
| Bash runs | `after-bash` | Catches wiki edits and commits made in the shell | — |
| The answer ends | `wiki-sync` | Brings the graph up to date, however pages were edited | — |
| The answer ends | `answer-check` | Checks the answer: re-asks, the work report, length, prose | once |
| The answer ends | `checklist-check` | Checks that every checklist item is done | once |

## When an answer is sent back

Two gates can send an answer back to Claude before it reaches you: `answer-check` and `checklist-check`.
Claude Code then shows `Stop hook feedback:` with the reason, and Claude fixes the answer or finishes
the open items. Each gate does this **once a turn**; on the second try it only reports what is left,
so a turn can never loop.

## When a gate cannot decide

It lets the turn pass. A gate that crashes would break every session its event fires in, so every gate
exits cleanly on input it does not understand.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
