#!/bin/sh
# Scaffold a wiki for one topic.
#
#   new-topic.sh <topic> ["one-line description"]
#
# Creates <root>/<topic>/{README.md,wiki/{index.md,log.md},raw/}.
# Re-running is safe: existing files are left alone, missing ones are filled in.
# That matters because the usual failure is a topic folder that has pages but no
# index.md — the pages then cannot be found, which is the same as not having them.
#
# Root resolution order, so nothing is hardcoded to one machine:
#   $LLM_WIKI_ROOT  ->  $HOME/llm-wiki-docs
set -eu

TOPIC="${1:-}"
DESC="${2:-}"

if [ -z "$TOPIC" ]; then
  echo "usage: new-topic.sh <topic> [\"one-line description\"]" >&2
  echo "  topic: lowercase-with-hyphens, named after what the knowledge is about" >&2
  exit 64
fi

case "$TOPIC" in
  */*|.|..|-*)
    echo "error: topic must be a single name, not a path: '$TOPIC'" >&2
    exit 64 ;;
esac

ROOT="${LLM_WIKI_ROOT:-$HOME/llm-wiki-docs}"
DIR="$ROOT/$TOPIC"
TODAY="$(date +%Y-%m-%d)"

mkdir -p "$DIR/wiki" "$DIR/raw"

created=""
note() { created="$created  created $1\n"; }

if [ ! -e "$DIR/README.md" ]; then
  cat > "$DIR/README.md" <<README
# $TOPIC

${DESC:-<one line: what this topic is about>}

## Layout

- \`wiki/\` — my own words. Start at \`wiki/index.md\`.
- \`raw/\` — sources as received. Never edited.

## Conventions

- One thing, one page. Same subject -> update that page, never a near-duplicate.
- \`wiki/index.md\` lists every page, one line each. Not in the index = not findable.
- \`wiki/log.md\` is append-only: \`## [YYYY-MM-DD] <ingest|query|lint> | <title>\`.
- Cross-link with \`[[wikilinks]]\`. A link to a missing page marks a gap worth filling.
- Numbers carry their provenance: how measured, dataset, filters, n, and the result file path.
README
  note "$DIR/README.md"
fi

if [ ! -e "$DIR/wiki/index.md" ]; then
  cat > "$DIR/wiki/index.md" <<INDEX
# $TOPIC — index

> One line per page. Search this first, before reading raw sources.

## Overview

_(nothing yet)_
INDEX
  note "$DIR/wiki/index.md"
fi

if [ ! -e "$DIR/wiki/log.md" ]; then
  cat > "$DIR/wiki/log.md" <<LOG
# $TOPIC — log

Append-only. Newest at the bottom.

## [$TODAY] lint | topic created
- pages touched: README.md, wiki/index.md
- note: empty wiki scaffolded. Nothing ingested yet.
LOG
  note "$DIR/wiki/log.md"
fi

[ -e "$DIR/raw/.gitkeep" ] || { : > "$DIR/raw/.gitkeep"; note "$DIR/raw/.gitkeep"; }

echo "topic ready: $DIR"
if [ -n "$created" ]; then
  printf "%b" "$created"
else
  echo "  (all files already existed — nothing changed)"
fi
