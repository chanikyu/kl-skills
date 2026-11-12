<div align="center">

<img src="assets/hero.png" alt="kl-skills — Skills and hook gates for Claude Code, installed together. Two install commands and the banner that appears after a restart." width="100%" />

<br />

<img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
<img src="https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-57606A" alt="macOS, Linux, Windows" />

**English** · [한국어](docs/ko-KR/README.md) · [日本語](docs/ja-JP/README.md) · [简体中文](docs/zh-CN/README.md) · [Español](docs/es/README.md)

[Install](#install) · [Get started](#get-started) · [What's inside](#whats-inside) · [What's new](#whats-new)

</div>

<br />

## At a glance

Claude Code forgets what it learned when a conversation ends, and in a long conversation it drifts from rules like "keep it plain".

kl-skills keeps what Claude learns in a wiki and brings it back in later conversations. The rules go into hooks that check every answer.

<img src="assets/turn-flow.png" alt="One turn: the session starts, a message comes in, files are written, Bash runs, the answer ends. Each moment runs its hook gates." width="100%" />

| Included | Count | What it does |
| --- | --: | --- |
| Skills | 9 | Wiki, plain answers, code rules, planning, debugging, literature research |
| Hook gates | 9 | Answer checks, wiki upkeep, prose and code checks, plan drift |

<br />

## Install

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

Restart the session. The first line should read:

```
KL-SKILLS GATES v<version> — loaded, 9 rules enforced
```

> [!IMPORTANT]
> Most gates are written in Python. Without `python3` they skip quietly.

> [!NOTE]
> The gates' messages and the writing rules are Korean-first. English text is checked for undefined acronyms and long sentences only.

**Update** — `claude plugin marketplace update kl-skills`, then `claude plugin update kl-skills@kl-skills`, then restart.<br />
**Uninstall** — `claude plugin uninstall kl-skills@kl-skills`. Your wiki in `~/llm-wiki-docs/` stays.

<br />

## Get started

Start from what you want to do. A skill loads when the conversation matches it; you can also name it.

| You want to | Say | Skill |
| --- | --- | --- |
| Keep what you learned | "Put this in the wiki" | `llm-wiki-docs` |
| Use what the wiki knows | nothing — every message is matched against the wiki | `wiki-recall` |
| See the whole wiki | "Show me the wiki graph" | `graph-doc-memory` |
| Research a question | "Research whether X causes Y" | `research-to-wiki` |
| Plan a project | "Plan this with the planner" | `planner` |
| Find why something broke | "Find the cause of this error" | `pipeline-debug` |
| Write code | nothing — naming, comment and no-hardcoding rules apply | `readable-code` · `no-hardcoding` |

When a gate blocks an answer, Claude Code shows `Stop hook feedback:` with the reason, and Claude rewrites the answer. Only `answer-check` blocks, and only once a turn.

<br />

## What's inside

<img src="assets/parts.png" alt="Your message goes to Claude Code, which reads skills, is checked by hook gates and keeps what it learns in the wiki." width="100%" />

### Skills

| Skill | What it does |
| --- | --- |
| `llm-wiki-docs` | Keeps what you learn in a wiki, one page per topic |
| `wiki-recall` | Finds related wiki pages and uses them in the answer |
| `graph-doc-memory` | Draws the whole wiki as a graph in the browser |
| `research-to-wiki` | Records research with each source's study type and how much of it was read |
| `natural-answering` | Writes without skipping terms, baselines or the step to the conclusion |
| `readable-code` | Names say what they hold; comments say why |
| `no-hardcoding` | Keeps lists, paths and thresholds out of the code |
| `pipeline-debug` | Finds the first stage that went wrong, not the line that failed |
| `planner` | Plans by field and horizon, and flags work that drifts from the plan |

### Hook gates

| When | Gate | What it does |
| --- | --- | --- |
| Session starts | `session-start` | Prints the banner |
| A message comes in | `wiki-recall` | Attaches related wiki pages |
| A file is written | `wiki-index-check` | Flags a wiki page missing from the index |
| A file is written | `wiki-graph` | Redraws the wiki graph |
| A file is written | `prose-check` | Flags hard-to-read spots in wiki pages |
| A file is written | `code-check` | Flags vague Python names and missing docstrings |
| A file is written | `plan-drift` | Checks a plan's frame and drift |
| Bash runs | `after-bash` | Catches wiki edits and commits made in the shell |
| The answer ends | `wiki-sync` | Brings the graph up to date, however pages were edited |
| The answer ends | `answer-check` | Checks the answer and blocks once if needed |

<br />

## What's new

0.17 to 0.20 were released on 2026-11-11, 0.21 on 2026-11-12. Full history: `git log`.

- **0.21** — the maintainers' skills (`plugin-release`, `hook-replay`) left the plugin; README in five languages
- **0.20** — a turn that changed files must end with a six-step work report
- **0.19** — `hook-replay`, `plugin-release` and `research-to-wiki`
- **0.18** — blocks only when you really asked again; plan drift and wiki recall
- **0.17** — `planner`

<br />

## Requirements

| Needs | For | Without it |
| --- | --- | --- |
| `python3` | most gates and every skill script (standard library only) | those gates skip quietly |
| `git` | plan drift checks | that check is skipped |

Prebuilt gates ship for macOS (Apple silicon and Intel), Linux (x86_64 and ARM, also WSL) and Windows (x86_64). On anything else the gates pass silently.

<br />

## Security

- Gates and skill scripts use no network.
- The wiki, its graph and your plans stay on your machine.
- When a gate cannot decide, it lets the turn pass.

<br />

## Development

Releasing, testing hooks on real conversations, the hook output contract and the file map: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## License

MIT
