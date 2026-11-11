---
name: llm-wiki-docs
description: Compile research, coding plans, and analysis results into a living wiki under ~/llm-wiki-docs/<topic>/wiki/ instead of writing one-off documents — raw sources stay untouched, one topic gets one page that is updated in place, and index.md plus an append-only log.md are always maintained. Use this whenever you are about to write or update any document, note, report, plan, research summary, knowledge file, or memory, when you are asked to "정리해줘 / 문서로 남겨 / 기록해둬 / 노트 만들어", when an analysis or investigation produces findings worth keeping, or when you are about to create a new file on a topic that may already have a page. Also use it when answering a question that the wiki may already cover, so the answer comes from the wiki rather than from scratch. Triggers - document, documentation, write-up, notes, note-taking, report, research summary, knowledge base, wiki, vault, second brain, memory, index, changelog, 문서 작성, 문서화, 노트 정리, 지식 정리, 위키, 리서치 정리, 분석 결과 정리, 코딩 계획, 기록 남기기, 메모리 저장.
---

# LLM Wiki Docs

Most documentation dies because it is written once and never updated, so the next
question gets answered from raw sources again. This skill does the opposite: knowledge is
**compiled once into a wiki and kept current**, so explorations compound instead of
evaporating.

Source of the pattern: Karpathy's "LLM Wiki" gist. A faithful summary, with the parts that
shape the rules below, is in `references/karpathy-llm-wiki.md` — read it when you need the
rationale or the optional tooling (Obsidian, qmd, git).

## Where it lives

All wikis live under one root so that nothing gets lost in scattered project folders:

```
~/llm-wiki-docs/<topic>/
├── README.md        the schema: what this topic is, its conventions, where things go
├── wiki/            your own words. index.md + log.md + one page per thing
│   ├── index.md     catalog: every page, one line each, grouped by category
│   ├── log.md       append-only history
│   └── *.md         the pages
└── raw/             sources as received. never edited
```

`<topic>` is the thing the knowledge is *about*, in lowercase-with-hyphens: a tool being
built (`bacdive-answer-table`), a research question (`gut-metabolite-coupling`), a system
being learned. Prefer an existing topic over a new one — a second topic for the same subject
splits the knowledge and neither half stays current. The root is overridable with
`LLM_WIKI_ROOT` for machines that keep it elsewhere.

**Project code stays in the project repo.** The wiki holds understanding, decisions, and
findings, and points at the code by path. Copying code into the wiki creates a second,
rotting copy.

## The line between this wiki and a project's own docs

A project has its own documents — README, architecture, API reference, developer guide,
troubleshooting. Those are a different thing from a wiki page, and this is the canonical
rule for which is which. (The project-doc side, including the skeleton each kind of document
uses, is in the `natural-answering` skill: `references/document-structure.md`.)

**Do not split them by where the writing came from.** "Summarise the project's README into a
wiki page" sounds tidy and produces the worst document in the repository. The same fact now
lives twice. The README gets updated, the summary does not, and the stale half is the one
that reads like a conclusion. That is the drift `source-of-truth.md` exists to prevent.

Split them by one question instead:

> **Does this writing have to change when the code changes?**

| Answer | Where it goes | What is canonical |
|---|---|---|
| Yes | the project's own docs | the code |
| No | this wiki | the wiki page |

Concretely:

| The writing | Where |
|---|---|
| README, API reference, developer guide | project |
| architecture as it currently stands | project |
| troubleshooting: this symptom, this fix | project |
| how to run the pipeline, with its parameters | project |
| **why A was chosen over B, and whether that reason still holds** | wiki |
| **a result with its conditions** — value, how measured, dataset, filters, n, result file | wiki |
| **a metric that was abandoned mid-measurement, and what broke it** | wiki |
| a paper, a database, a tool: what it is and where it bites | wiki |

So a wiki page **points at** a project document rather than summarising it. One line is
enough: "how to run it is in `<repo>/docs/pipeline.md`". The page then holds what that
document does not — why it was built that way, and what was never checked.

### When to touch the wiki

"Whenever something important happens" has no edge, so in practice either nothing gets
filed or everything does. Three events, and nothing else:

1. **A decision was made** — what was chosen, what was rejected, why, and what would
   invalidate the reason
2. **A number came out** — with the six columns `stable-claims.md` requires
3. **Something was learned that outlives this project** — a tool's trap, an external
   dataset's conditions

Outside those three, update the project's docs and leave the wiki alone.

**The direction is not always project → wiki.** In research the wiki usually comes first.
Papers are read and the approach is settled before any code exists, so the project's docs
are derived from the wiki rather than the other way round. The rule above does not care
which came first. It only asks whether the writing ages with the code.

## Scripts

Use these rather than editing `index.md` and `log.md` by hand. Not because hand-editing is
forbidden, but because it is what gets skipped under time pressure, and because a hand-typed
entry drifts from the format — after which `lint.py` stops recognising it and the page goes
quietly missing from the catalog.

All of them resolve the root the same way: `$LLM_WIKI_ROOT`, else `~/llm-wiki-docs`.

```bash
# create a topic — safe to re-run, never overwrites, refills anything missing
scripts/new-topic.sh <topic> ["one-line description"]

# file a page in the index — replaces the page's existing line instead of adding a second
scripts/index-add.py <topic> <page.md> <category> "one line on what it holds"

# append to the log — only ever adds at the bottom
scripts/log-append.py <topic> <ingest|query|lint> "<title>" \
    [--source raw/x.pdf] [--pages a.md,b.md] [--note "what changed in the understanding"]

# find the mechanical inconsistencies — no topic means every topic
scripts/lint.py [topic ...]
```

After `new-topic.sh`, `git init` inside the topic if the knowledge is worth a history
(usually yes — the diffs show how the understanding changed, which the pages themselves
cannot).

`lint.py` reports five things, all pure comparisons, so the answer is identical every run:
pages missing from the index, index entries whose file is gone, a page listed twice, links
to pages that do not exist, and pages nothing links to. It exits 1 when it finds anything.
Judgement calls — stale claims, contradictions — are deliberately not in it; those need
reading, and the `lint` operation below is where they belong.

A `[[link]]` to a page that does not exist is **not automatically a defect**: it may be a
deliberate marker for a gap worth filling. `lint.py` lists them so the two can be told
apart, not so they can be deleted.

### The index hook

A `PostToolUse` hook (`wiki-index-check`) watches writes under `~/llm-wiki-docs/<topic>/wiki/`
and says so when the page is not in that wiki's `index.md`. It warns and never blocks, so a
page can be written first and filed a moment later — but if the warning is still showing when
the work is done, the page is unfindable and the warning is the last chance to notice.

## The three operations

Name the operation you are doing, because each has a different ending condition.

### Ingest — a source arrives, or something is learned

1. Read the source. Put the original in `raw/` if it is a file; otherwise record its URL.
2. Say the takeaways plainly first, in your own words. If you cannot restate it, you have
   not understood it yet and the page will just be a quote dump.
3. Write or update the page for it, citing back to the raw source.
4. **Revise every page this touches.** One real ingest usually edits 10–15 pages, not one:
   the new source changes what neighbouring pages should say. Updating only the new page is
   the most common way a wiki goes stale.
5. Cross-link with `[[wikilinks]]`. A link to a page that does not exist yet is useful — it
   marks a gap worth filling.
6. Update `index.md` and append to `log.md` — use the scripts below rather than
   hand-editing, so the entry format stays machine-readable.
7. Where the new source contradicts an existing page, **write the contradiction down** on
   both pages rather than silently picking a side. Which one is right is often the next
   thing worth investigating.

### Query — answer from the wiki

Search `index.md` first, read the pages it points to, then answer with citations. Do not
re-read the raw sources each time; that is the loop this skill exists to break.

If the answer turned out to be worth having, file it back as a new or updated page. An
answer that only lives in a chat log is gone next session.

### Lint — periodic health check

Scan for: contradictions, claims that have gone stale, orphan pages nothing links to,
concepts referred to but never written, and missing cross-references. Then propose the next
questions worth investigating and sources worth ingesting. Lint is where a wiki earns its
keep — it turns "what do I not know yet" into a list.

## Page kinds

A page is one thing, named after that thing. Common kinds:

| Kind | Holds | Named after |
|---|---|---|
| Source summary | one paper, doc, video, thread | the source |
| Entity | a tool, organism, dataset, person, system | the entity |
| Concept | a mechanism, method, definition | the concept |
| Comparison | two or more options weighed | what is compared |
| Overview | the entry point for a topic | the topic |
| Coding plan | what is being built, why, and the decisions made | the feature or tool |
| Analysis result | a finding, with how it was measured | the question answered |

**Coding plans** record the decisions and the reasons, not a task checklist that goes stale
in a day. The valuable part six months later is "we chose X over Y because Z", and whether Z
still holds.

**Analysis result pages must stay honest about where numbers came from.** Record for each
number: the value, how it was measured (package.function and key arguments), the dataset,
the filters or gates applied, n, and **the path to the result file**. Without the source file
path the number cannot be checked later, and a number that cannot be checked quietly drifts
every time it is re-quoted. The result files themselves belong wherever the analysis saved
them (see the `analysis-artifacts` skill) — the wiki cites those paths, it does not copy the
data.

## What keeps this from rotting

- **Raw is immutable.** Never edit anything in `raw/`. Your reading of it goes in `wiki/`.
- **One thing, one page.** Same subject → update that page. A near-duplicate file means two
  versions of the truth and only one of them will get fixed.
- **`log.md` is append-only.** Never rewrite history; add to the bottom. Entries use a
  grep-able prefix so the history can be searched:
  `## [YYYY-MM-DD] ingest | <title>`, likewise `query |` and `lint |`.
- **`index.md` is the front door.** If a page is not in the index, it will not be found, and
  an unfindable page is the same as no page.
- **Cite, and separate what is documented from what you inferred.** "The source says X" and
  "I think X follows" are different claims; a reader six months later cannot tell them apart
  unless the page does.

## Templates

`index.md`:

```markdown
# <topic> — index

> One line per page. Search this first.

## Overview
- [overview](overview.md) — what this topic is and where to start

## <category>
- [page-name](page-name.md) — one line on what it holds
```

`log.md`:

```markdown
# <topic> — log

Append-only. Newest at the bottom.

## [2026-11-11] ingest | <title>
- source: raw/<file> or <url>
- pages touched: a.md, b.md, index.md
- note: what changed in the understanding, not just which files moved
```
