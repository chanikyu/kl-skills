# Developing kl-skills

For whoever changes and releases this plugin. Users need only the [README](../README.md).

Two skills are for maintainers only and live in this repository, not in the plugin: `plugin-release` and
`hook-replay` under `.claude/skills/`. Claude Code loads them when you work in this repository; people who
install kl-skills never see them.

- [Releasing a change](#releasing-a-change)
- [Checking a hook on real conversations](#checking-a-hook-on-real-conversations)
- [Hook output contract](#hook-output-contract)
- [Adding a hook](#adding-a-hook)
- [Rust or Python](#rust-or-python)
- [Why there is a Stop gate](#why-there-is-a-stop-gate)
- [Build and test](#build-and-test)
- [README images](#readme-images)
- [File map](#file-map)

## Releasing a change

`claude plugin update` looks only at `version` in `.claude-plugin/plugin.json`. If the version did not
change, nothing is updated. The `plugin-release` skill keeps the order that gets a change to the installed copy:

```sh
python3 .claude/skills/plugin-release/scripts/release.py bump X.Y.Z   # every file that carries the version
# run the tests, commit, push
python3 .claude/skills/plugin-release/scripts/release.py ship         # waits for CI, installs only if it passed, then verifies
# restart the session, then
python3 .claude/skills/plugin-release/scripts/release.py verify
```

- Doing it by hand skips steps. On 2026-11-11 an install ran before CI finished and froze an old binary in the cache.
- `version-files.txt` lists the other files that carry the version (`crates/kl-gate/Cargo.toml`), so the banner
  always names the installed version.
- CI runs only for commits that touch `crates/`, `hooks/`, `Cargo.toml` or the workflow. `ship` sees when a commit
  touches none of them (skills or docs only) and installs without waiting.
- A frozen binary cannot be fixed by updating, because the version number is the same. `verify` says so;
  uninstall and install again. Check `~/.claude/plugins/data/kl-skills/` first.
- Docs-only changes need no version bump. The installed copy does not read the README.

## Checking a hook on real conversations

Fixtures hold only the conversations their author imagined. Real transcripts carry compaction summaries, rule
dumps, resent messages and pasted code. `hook-replay` replays one gate at every message the person typed, as it
would have run at that moment, and writes one row per moment to a TSV:

```sh
python3 .claude/skills/hook-replay/scripts/replay.py answer-check --transcript ~/.claude/projects/<project>/<session>.jsonl \
  --out replay_answer-check_stop_all.tsv            # --event prompt for UserPromptSubmit gates, --last N for the tail
```

Run it after changing a gate that reads the conversation (`answer-check`, `wiki-recall`, `wiki-sync`), before
releasing it. It is how the answer-check and wiki-recall false positives of 2026-11-11 were found and counted.

## Hook output contract

- The gate name is `argv[1]`; the event (JSON) comes on stdin.
- Plain stdout mostly does not reach the model. `SessionStart` output does; `PostToolUse` and `Stop` stdout
  only lands in the debug log. To tell the model, print one JSON object:
  `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "..."}}`.
  Python gates use `tell_model` in `hooks/py/_hook_output.py`; the Rust gate uses `model_note`.
- To block at `Stop`, print `{"decision": "block", "reason": "..."}`. `answer-check` blocks once and lets the
  retry through (`stop_hook_active`), so it cannot loop.
- Until 2026-11-11 four gates' findings went only to the debug log, because an earlier README said stdout reached the model.
- When unsure, exit 0. A gate that crashes breaks every session that event fires in. The launchers
  (`run.sh`, `run.ps1`) follow the same rule.

## Adding a hook

**Python** — create `hooks/py/<gate>.py` and register it in `hooks/hooks.json` as `run.sh <gate>`. No build.

**Rust** — add a branch to `match event` in `crates/kl-gate/src/main.rs` and register it in `hooks/hooks.json`.
Push, and CI builds the five targets and commits them to `bin/`.

The launcher prefers `hooks/py/<gate>.py` when it exists and falls back to the Rust binary. Deleting the `.py`
hands the gate to Rust without touching `hooks.json`.

## Rust or Python

| | Rust | Python |
| --- | --- | --- |
| Needs on the user's machine | nothing (the binary ships in the repo) | `python3` |
| Change and check | about a minute of CI | immediate |
| One hook start | 4.5 ms | 32.0 ms |

Medians of 30 runs on an Apple silicon Mac: `scripts/bench-hook-startup.py`,
`results/hook-startup_macos-arm64_n30_20261111.txt`. Both include process start, so the difference, 27.5 ms, is
what matters. Once a session it goes unnoticed; on every tool call it adds up (100 Bash calls, about 2.8 s).
Python for gates that run a few times a session or handle a lot of text; Rust for gates on every tool call
and rules that must run on Windows.

## Why there is a Stop gate

`PostToolUse` fires only for `Write` and `Edit`, but the model also writes files with Bash (heredocs, `sed`,
short scripts). Those edits pass every file gate. On 2026-11-11 a session wrote a whole research result through
Bash and no gate ran. Gating Bash itself is costly: it is the most used tool and its shell variables cannot be
resolved. So `wiki-sync` runs once a session and asks the file system which pages are newer than `graph.json`.

`wiki-index-check` is Rust because it runs on every file write and usually exits after reading one path.
`wiki-graph` and `prose-check` are Python because their real work (the graph builder, the prose checker) is
Python; a Rust gate would only add a process.

## Build and test

```sh
cargo test                                        # the Rust gate's decision logic
for t in tests/selftest*.sh; do sh "$t"; done     # every selftest
claude plugin validate .                          # plugin and skill format
```

The five targets build in CI (Windows and macOS SDK licences). For skills or docs changes CI does not run, so run
the selftests yourself.

## README images

`assets/*.png` are drawn in VectorCraft by `assets/src/figures.py` (layout) and `assets/src/figures.json` (words,
colours, fonts); gate names, skill names and the version come from the repo. The hero shows the banner with the
version, so redraw it when releasing. How: `assets/src/README.md`. Do not edit the PNGs by hand.

## File map

```text
.claude-plugin/      plugin.json · marketplace.json
.claude/skills/      maintainers only, not shipped: plugin-release (release.py — bump · ship · verify) · hook-replay (replay.py)
assets/              README images; assets/src/ holds figures.py · figures.json and each figure's .vectorcraft · .svg · .pdf
docs/                DEVELOPMENT.md (this file) · <language>/README.md (ko-KR, ja-JP, zh-CN, es)
  wiki/              the documentation wiki: Home, Installation, How-it-works, one page per skill,
                     each in five languages (<page>.md and <page>-ko/-ja/-zh/-es.md) · _Sidebar · _Footer
skills/
  llm-wiki-docs/     wiki convention — new-topic.sh · index-add.py · log-append.py · lint.py
  graph-doc-memory/  graph DB and viewer — build_graph.py · open-graph.sh · viewer.html
  no-hardcoding/     keep values out of code
  pipeline-debug/    probe.py — counts, columns and blanks of the file between stages
  planner/           check_plan.py · check_drift.py · plan template · field references
  wiki-recall/       recall.py — two-letter fragments + BM25 + query coverage + graph neighbours
  readable-code/     check_code.py — Python names and docstrings
  natural-answering/ check_prose.py · data/ (rules) · references/ (work report, document skeletons)
  research-to-wiki/  check_research.py · data/ (evidence and reading levels) · page template
  task-checklist/    the checklist procedure the checklist gates point to
hooks/
  hooks.json         which gate runs on which event
  run.sh · run.ps1   launchers: the Python gate if present, else the Rust binary
  py/                Python gates and shared modules (_transcript · _work_files · _hook_output · _checklist)
  data/              skill-match word lists: skill-match-generic.txt (too common to count) · skill-match-skip.txt
crates/kl-gate/      the Rust gate
bin/                 five prebuilt binaries — CI fills it
version-files.txt    other files that carry the version
scripts/ · results/  hook start-up benchmark and its results
tests/
  selftest.sh                  the launcher picks the binary or the interpreter
  selftest-readme.sh           README and wiki counts, lists and links match the repo, in every language
  selftest-banner.sh           the banner's gate count matches hooks.json
  selftest-new-topic.sh        creating a wiki topic never overwrites
  selftest-wiki-scripts.sh     index, log and lint scripts
  selftest-wiki-sync.sh        pages edited in the shell are caught at session end
  selftest-wiki-touch.sh       the same, right after the Bash call
  selftest-wiki-recall.sh      the right page first, silence on unrelated messages
  selftest-graph.sh            graph counts and the viewer (opened in Chrome when present)
  selftest-prose.sh            omissions caught, clean writing silent
  selftest-readable-code.sh    vague names and missing docstrings
  selftest-code-check.sh       the same check as a hook
  selftest-answer-check.sh     re-asks, the work report, blocking once
  selftest-pipeline-debug.sh   a blank in the second stage shows up as a number
  selftest-planner.sh          plan frame, goal links and drift
  selftest-hook-replay.sh      moments are cut at the right line
  selftest-plugin-release.sh   no install when CI fails
  release_paths_check.py       (called by the test above) CI decisions per workflow shape
  selftest-research-to-wiki.sh source labels on research pages
  selftest-checklist.sh        an open item sends the answer back once; a finished list passes
  selftest-skill-match.sh      a message names its skill; everyday messages stay silent
```
