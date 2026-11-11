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

## Starting a topic

Run the scaffold rather than making the files by hand — `index.md` and `log.md` are exactly
what gets skipped when creating files manually, and a wiki without them degrades into a
folder of loose notes:

```bash
scripts/new-topic.sh <topic> ["one-line description"]
```

It is safe to re-run; it never overwrites an existing file. Then `git init` inside the topic
if the knowledge is worth a history (usually yes — diffs show how understanding changed).

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
6. Update `index.md` and append to `log.md`.
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
