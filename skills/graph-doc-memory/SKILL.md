---
name: graph-doc-memory
description: Turn every llm-wiki page under ~/llm-wiki-docs into one graph database and open it as an interactive, Obsidian-style graph view in the browser. Use this when asked to see, open, or show the knowledge graph, the document graph, the wiki map, or how the notes connect — "그래프 보여줘 / 그래프 열어줘 / 문서 연결 보여줘 / 지식 그래프 / 위키 지도" — and when asked to rebuild or refresh it. Also use it to answer questions the graph answers better than reading pages: which pages are hubs, which are orphans with no links, which [[links]] point at pages that do not exist yet, and which topics are connected to each other. The graph is rebuilt automatically by a hook whenever a wiki page is written, so it is normally already current; this skill is how it gets built on demand and opened. Triggers - graph, graph view, knowledge graph, document graph, interactive graph, node, link, backlink, orphan, hub, missing page, wiki map, 그래프, 그래프 뷰, 지식 그래프, 노드, 링크, 백링크, 고아 문서, 끊어진 링크, 문서 지도, 위키 그래프.
---

# Graph Doc Memory

The `llm-wiki-docs` skill makes pages and `[[links]]`. Those links are already a graph, but
nothing reads it as one, so the questions a graph answers best stay unanswered: what is this
wiki's centre of gravity, what did I write and never link to, what did I keep linking to and
never write. This skill compiles the links into a database and draws it.

Depends on the wiki layout the `llm-wiki-docs` skill creates. Read that skill if the wiki
does not exist yet — build the pages first, there is nothing to graph otherwise.

## Two artifacts, one build

```
<root>/.graph/
├── graph.json   the database — nodes, links, degrees, stats. Read this to answer questions.
└── graph.html   the viewer, with the data inlined. Open this to look at it.
```

`<root>` is `$LLM_WIKI_ROOT`, or `~/llm-wiki-docs`. Both files are **build artifacts**:
regenerated on every build, never edited by hand. The pages are the source of truth.

The data is inlined into the viewer because a `file://` page cannot `fetch()` a sibling
`.json` — browsers treat each local file as its own origin. Inlining is what lets the graph
open as a plain double-click, with no local server, no port, and no process left running.

## Opening it — only when asked

```bash
scripts/open-graph.sh            # rebuild, then open in the default browser
scripts/open-graph.sh --no-build # open what is already built
```

**Do not open a browser window unless the user asked to see the graph.** Rebuilding is
cheap and silent; opening a tab is not. When the question is about the graph's *contents*
rather than its picture, read `graph.json` instead and answer from it.

## Rebuilding without opening

```bash
scripts/build_graph.py [--root DIR] [--out DIR] [--quiet]
```

Prints a one-line summary: topics, pages, links, missing pages, orphans. This is also what
the hook runs, so running it by hand and letting the hook run are the same operation.

## Automatic updates

`hooks/py/wiki-graph.py` runs on PostToolUse for Write/Edit. If the written file is
`<root>/<topic>/wiki/**/*.md` it rebuilds the graph; for every other file it exits
immediately. So a page written by the `llm-wiki-docs` skill lands in the graph in the same
turn, without anyone remembering to refresh it.

If the graph looks behind the wiki, the hook is not running — check `/plugin`, then run the
builder by hand. The graph being stale is a hook problem, never a reason to stop writing pages.

## What is a node, what is a link

- **Node** — one page under `<topic>/wiki/`, id `<topic>/<page>`. `raw/` is sources and the
  topic `README.md` is the schema doc; neither is knowledge, so neither is a node.
- **Link** — `[[page]]`, `[[page|alias]]`, `[[page#heading]]`, and `[text](page.md)`.
  Targets inside code fences and inline code are examples, not links, and are ignored.
- **Resolution order** — same topic first, then `<topic>/<page>` written out in full, then a
  bare name that exists in exactly one other topic. That last rule is what makes the whole
  root one graph rather than one island per topic.
- **Missing pages stay in the graph**, drawn as dashed circles. A link to an unwritten page
  is a gap worth filling, which is exactly the thing worth seeing.

## Answering from graph.json

`graph.json` is the cheaper way to answer most graph questions — no browser needed.

| Question | Field |
|---|---|
| Which pages are hubs? | highest `in` |
| What is orphaned? | `in == 0 && out == 0` |
| Which links are broken? | nodes with `exists: false` |
| How big is this wiki? | `stats` |
| What links to this page? | `links` where `target` is it |

When a number from here goes into a report, cite the file path and the `generated`
timestamp — the graph is a snapshot, and the wiki moves.

## The viewer

Obsidian's graph view, with its controls: search filter, orphan and missing-page toggles,
link arrows, node size, link thickness, text fade threshold, and the four forces (centre,
repel, link force, link distance). Topics are the colour groups. Local graph mode shows only
what is connected to the selected node, out to a depth you set.

Click a node for its path, its outbound links, and its backlinks; the path is a `file://`
link to the page itself. Hover highlights the neighbourhood, scroll zooms, drag pans, and
dragging a node pins it. `Esc` clears the selection.
