**English** · [한국어](wiki-recall-ko.md) · [日本語](wiki-recall-ja.md) · [中文](wiki-recall-zh.md) · [Español](wiki-recall-es.md)

[Home](Home.md) · [Installation](Installation.md) · [How it works](How-it-works.md)

# wiki-recall

Pulls what the wiki already knows into the answer instead of working it out again.

## Use it in Claude

Nothing to say: a hook searches the wiki on every message. Ask "What did we decide about X?" to go deeper than the attached lines.

## What it does

1. For every message, the hook attaches the paths and key lines of clearly related pages — at least two shared words and 40% of the question's weight covered. Unrelated messages get nothing.
2. To go deeper, Claude reads the pages. When the whole wiki is small (30,000 characters or less) it reads all of it (CAG); otherwise it picks the best pages (RAG: BM25, question coverage, graph neighbours).
3. Korean is matched in two-letter pieces; a one-letter word counts only where it stands alone.

## Files and scripts

| Script | Does |
| --- | --- |
| `recall.py "question" [--mode auto\|cag\|rag] [--top 3] [--min-coverage 0.4]` | Searches the wiki |

Stop words, particles and common pieces are data files in `data/`. `WIKI_RECALL_MIN_COVERAGE` changes the threshold.

## Hooks that back it

The `wiki-recall` gate runs on every message.

## Limits

Attached lines are excerpts chosen by search. Open the page before quoting it.

---

[kl-skills](../../README.md) · MIT licensed · made for [Claude Code](https://claude.com/claude-code)
