<div align="center">

<img src="assets/hero.png" alt="kl-skills — Skills and hook gates for Claude Code, installed together. Two install commands and the banner that appears after a restart." width="100%" />

<br />

<img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
<img src="https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-57606A" alt="macOS, Linux, Windows" />
<a href="https://github.com/chanikyu/kl-skills/wiki"><img src="https://img.shields.io/badge/docs-wiki-2F6FEB" alt="Documentation wiki" /></a>

**English** · [한국어](docs/ko-KR/README.md) · [日本語](docs/ja-JP/README.md) · [简体中文](docs/zh-CN/README.md) · [Español](docs/es/README.md)

[Install](#install) · [Skills](#skills) · [Hook gates](#hook-gates) · [Wiki](https://github.com/chanikyu/kl-skills/wiki)

</div>

<br />

## At a glance

Claude Code forgets what it learned when a conversation ends, and in a long conversation it drifts from rules like "keep it plain".

kl-skills keeps what Claude learns in a wiki and brings it back later. The rules go into hooks that check every turn.

<img src="assets/turn-flow.png" alt="One turn: the session starts, a message comes in, files are written, Bash runs, the answer ends. Each moment runs its hook gates." width="100%" />

| Included | Count | What it does |
| --- | --: | --- |
| Skills | 10 | Wiki, plain answers, code rules, checklists, planning, debugging, research |
| Hook gates | 12 | Skill matching, checklists, answer checks, wiki upkeep, prose and code checks |

<br />

## Install

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

Restart the session. The first line should read:

```
KL-SKILLS GATES v<version> — loaded, 12 rules enforced
```

> [!IMPORTANT]
> Most gates are written in Python. Without `python3` they skip quietly.

> [!NOTE]
> The gates' messages and the writing rules are Korean-first. English text is checked for undefined acronyms and long sentences only.

Requirements, update and uninstall: [Installation](https://github.com/chanikyu/kl-skills/wiki/Installation).

<br />

## Skills

<img src="assets/parts.png" alt="Your message goes to Claude Code, which reads skills, is checked by hook gates and keeps what it learns in the wiki." width="100%" />

Each name opens its wiki page: when it applies, what to say, and what it does.

| Skill | What it does |
| --- | --- |
| [`llm-wiki-docs`](https://github.com/chanikyu/kl-skills/wiki/llm-wiki-docs) | Keeps what you learn in a wiki, one page per topic |
| [`wiki-recall`](https://github.com/chanikyu/kl-skills/wiki/wiki-recall) | Finds related wiki pages and uses them in the answer |
| [`graph-doc-memory`](https://github.com/chanikyu/kl-skills/wiki/graph-doc-memory) | Draws the whole wiki as a graph in the browser |
| [`research-to-wiki`](https://github.com/chanikyu/kl-skills/wiki/research-to-wiki) | Records research with each source's study type and how much of it was read |
| [`natural-answering`](https://github.com/chanikyu/kl-skills/wiki/natural-answering) | Writes without skipping terms, baselines or the step to the conclusion |
| [`readable-code`](https://github.com/chanikyu/kl-skills/wiki/readable-code) | Names say what they hold; comments say why |
| [`no-hardcoding`](https://github.com/chanikyu/kl-skills/wiki/no-hardcoding) | Keeps lists, paths and thresholds out of the code |
| [`task-checklist`](https://github.com/chanikyu/kl-skills/wiki/task-checklist) | Turns every instruction into a checklist and finishes only when every item is done |
| [`planner`](https://github.com/chanikyu/kl-skills/wiki/planner) | Plans by field and horizon, and flags work that drifts from the plan |
| [`pipeline-debug`](https://github.com/chanikyu/kl-skills/wiki/pipeline-debug) | Finds the first stage that went wrong, not the line that failed |

A skill loads when Claude judges the conversation matches it, which is not guaranteed. The `skill-match` gate names the fitting skill on every message, and you can always name it yourself.

<br />

## Hook gates

| When | Gate | What it does |
| --- | --- | --- |
| Session starts | `session-start` | Prints the banner |
| A message comes in | `wiki-recall` | Attaches related wiki pages |
| A message comes in | `skill-match` | Names the skill this message is for |
| A message comes in | `checklist-start` | Says where to write this instruction's checklist |
| A file is written | `wiki-index-check` | Flags a wiki page missing from the index |
| A file is written | `wiki-graph` | Redraws the wiki graph |
| A file is written | `prose-check` | Flags hard-to-read spots in wiki pages |
| A file is written | `code-check` | Flags vague Python names and missing docstrings |
| A file is written | `plan-drift` | Checks a plan's frame and drift |
| Bash runs | `after-bash` | Catches wiki edits and commits made in the shell |
| The answer ends | `wiki-sync` | Brings the graph up to date, however pages were edited |
| The answer ends | `answer-check` | Checks the answer and sends it back once if needed |
| The answer ends | `checklist-check` | Sends the answer back once if a checklist item is open |

When a gate sends an answer back, Claude Code shows `Stop hook feedback:` with the reason. More in [How it works](https://github.com/chanikyu/kl-skills/wiki/How-it-works).

<br />

## What's new

- **0.23** — field terms: `answer-check` flags words the field does not use, in answers and in slides (`data/domain-terms.tsv`)
- **0.22** — `task-checklist` with its two gates, `skill-match`, and this documentation wiki
- **0.21** — the maintainers' skills left the plugin; README in five languages
- **0.20** — a turn that changed files must end with a six-step work report
- **0.19** — `hook-replay`, `plugin-release` and `research-to-wiki`
- **0.18** — blocks only when you really asked again; plan drift and wiki recall

Full history: `git log`.

<br />

## Security

- Gates and skill scripts use no network.
- The wiki, its graph, your plans and checklists stay on your machine.
- When a gate cannot decide, it lets the turn pass.

## Development

Releasing, testing hooks on real conversations, the hook output contract and the file map: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## License

[MIT](LICENSE)
