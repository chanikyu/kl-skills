**English** · [한국어](graph-doc-memory-ko.md) · [日本語](graph-doc-memory-ja.md) · [中文](graph-doc-memory-zh.md) · [Español](graph-doc-memory-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# graph-doc-memory

Turns the whole wiki into one graph database and opens it as an interactive graph in the browser — only when you ask.

## Use it in Claude

Say "Show me the wiki graph".

## What it does

1. Every page under `<topic>/wiki/` is a node; every `[[link]]` or `[text](page.md)` is a link. Links to pages that do not exist yet stay in the graph as dashed circles — gaps worth filling.
2. The build writes `~/llm-wiki-docs/.graph/graph.json` and a self-contained `viewer.html` that opens over `file://` with no server.
3. The viewer: search, orphan and missing-page toggles, node size, link thickness, the four forces, and a local graph around the selected node. Click a node for its path, links and backlinks.

## Files and scripts

| Script | Does |
| --- | --- |
| `open-graph.sh [--root DIR] [--out DIR] [--no-build]` | Rebuilds the graph and opens the viewer |
| `build_graph.py [--root ROOT] [--out OUT] [--quiet]` | Rebuilds without opening |

## Hooks that back it

`wiki-graph` rebuilds the graph when a wiki page is written; `wiki-sync` catches shell edits when the answer ends.

## Limits

It never opens on its own. The graph is only as connected as the pages' links.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
