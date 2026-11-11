# Reference — Karpathy's "LLM Wiki"

Source: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
Read on 2026-11-11. This is a restatement of the gist, not the gist itself; the gist is the
authority. It is deliberately abstract — it says the exact structure is meant to be worked
out with your agent, which is what `SKILL.md` does.

## The problem it names

Most LLM document tools work by retrieval: fetch relevant chunks at query time and answer
from scratch, every time. Nothing accumulates. The same understanding is rebuilt on every
question, and contradictions between sources are never noticed because no two sources are
ever held side by side.

## The proposal

The LLM incrementally builds and maintains a persistent, interlinked wiki of markdown files
sitting between you and your raw sources. When a new source arrives it updates entity pages,
revises summaries, flags contradictions, and adds cross-references — so knowledge compounds.

## Three layers

| Layer | Who owns it | Rule |
|---|---|---|
| Raw sources | you curate | the LLM reads, never edits |
| The wiki | the LLM owns | generated markdown: summaries, entities, concepts, comparisons, overview |
| The schema | both refine it | a config doc (CLAUDE.md / AGENTS.md / README) defining structure, conventions, workflows |

## Three operations

- **Ingest** — add a source; the LLM summarizes it, updates the index, touches related pages
  (**often 10–15**), and logs the change. One at a time or in batches.
- **Query** — the LLM searches the wiki, reads the relevant pages, answers with citations.
  Good answers get filed back into the wiki as new pages.
- **Lint** — periodic health check: contradictions, stale claims, orphan pages, missing
  concepts, missing cross-references.

## Two special files

- `index.md` — a content-oriented catalog of every page: link plus a one-line summary,
  organized by category. Read first when answering a query.
- `log.md` — append-only chronological record of ingests, queries and lint passes. Consistent
  prefixes such as `## [date] ingest | Title` make it greppable.

## Optional tooling it suggests

- A local search tool (e.g. qmd) once the index alone stops being enough.
- Obsidian as a browsing front end: graph view, Web Clipper, local image downloads, Marp for
  slides, Dataview for frontmatter queries.
- Keep the wiki in a git repo for version history.

## Why it should work

The tedious part of a knowledge base is bookkeeping. People abandon it; LLMs do not mind
doing it. So the division of labour is: the human curates sources, directs analysis, and asks
questions; the LLM does the maintenance. The gist draws a loose line back to Vannevar Bush's
Memex.

Use cases it lists: personal tracking, deep research, reading-companion wikis for books, team
knowledge bases, due diligence.

## Noted trade-off

The gist's comment section includes substantive discussion of whether a compiled wiki actually
beats direct retrieval over raw sources for open-ended questions. Worth knowing that this is
contested rather than settled — the compiled wiki wins on compounding and contradiction
detection, retrieval wins when the corpus changes faster than the wiki can be maintained.
