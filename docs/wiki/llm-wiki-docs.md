**English** · [한국어](llm-wiki-docs-ko.md) · [日本語](llm-wiki-docs-ja.md) · [中文](llm-wiki-docs-zh.md) · [Español](llm-wiki-docs-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# llm-wiki-docs

Keeps what you learn in a wiki under `~/llm-wiki-docs/<topic>/wiki/`: one page per topic, written in your own words, with an index and a log.

## Use it in Claude

Say "Put this in the wiki". `skill-match` names the skill when a message asks for it. Claude also uses it after research or analysis worth keeping.

## What it does

1. Sources stay as they are in `raw/`. The wiki page is a new text, never an edited source.
2. One topic is one page. The same topic updates the existing page instead of starting a near-duplicate.
3. `index.md` holds one line per page and is searched first.
4. `log.md` is append-only: `## [YYYY-MM-DD] ingest | title`.
5. Pages link with `[[page]]`, and every claim points to its source.

What changes when the code changes stays in the project's own docs; what stays true goes to the wiki.

## Files and scripts

```text
~/llm-wiki-docs/<topic>/
  README.md      what the topic holds and where things go
  raw/           sources, untouched
  wiki/          pages, index.md, log.md
```

| Script | Does |
| --- | --- |
| `new-topic.sh <topic> ["description"]` | Creates the folders and an empty index and log, without overwriting |
| `index-add.py <topic> <page> <category> ["summary"]` | Adds a page to the index |
| `log-append.py <topic> ingest\|query\|lint "title" [--pages --source --note]` | Appends a log entry |
| `lint.py [topic]` | Finds pages missing from the index or the log, broken links and orphan pages |

`LLM_WIKI_ROOT` moves the root away from `~/llm-wiki-docs`.

## Hooks that back it

`wiki-index-check` flags a page missing from the index, `wiki-graph` redraws the graph, `prose-check` flags hard-to-read spots, and `wiki-sync` catches pages edited from the shell when the answer ends.

## Limits

The wiki lives on your machine only; nothing syncs it elsewhere.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
