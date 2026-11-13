**English** · [한국어](Home-ko.md) · [日本語](Home-ja.md) · [中文](Home-zh.md) · [Español](Home-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

<div align="center">

<img src="../../assets/hero.png" alt="kl-skills — Skills and hook gates for Claude Code, installed together." width="100%" />

</div>

# kl-skills wiki

Skills and hook gates for Claude Code, installed together. The skills say how a job is done; the hook
gates check that it was done; the wiki keeps what was learned.

## Skills

**Knowledge**

| Skill | What it does |
| --- | --- |
| [llm-wiki-docs](llm-wiki-docs.md) | Keeps what you learn in a wiki, one page per topic, with an index and a log |
| [wiki-recall](wiki-recall.md) | Finds related wiki pages for every message and uses them in the answer |
| [graph-doc-memory](graph-doc-memory.md) | Draws the whole wiki as a graph in the browser, when you ask |
| [research-to-wiki](research-to-wiki.md) | Records research with each source's study type and how much of it was read |

**Writing and code**

| Skill | What it does |
| --- | --- |
| [natural-answering](natural-answering.md) | Writes without skipping terms, baselines or the step to the conclusion |
| [readable-code](readable-code.md) | Names say what they hold; comments say why |
| [no-hardcoding](no-hardcoding.md) | Keeps lists, paths and thresholds out of the code |

**Work**

| Skill | What it does |
| --- | --- |
| [task-checklist](task-checklist.md) | Turns every instruction into a checklist and finishes only when every item is done |
| [planner](planner.md) | Plans by field and horizon, and flags work that drifts from the plan |
| [pipeline-debug](pipeline-debug.md) | Finds the first stage that went wrong, not the line that failed |

## Start here

- [Installation](Installation.md) — two commands, a restart, and how to check it worked
- [How it works](How-it-works.md) — when each hook gate runs, and which ones can send an answer back

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
