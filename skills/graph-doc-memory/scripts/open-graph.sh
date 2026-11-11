#!/bin/sh
# Rebuild the wiki graph and open it in the browser.
#
#   open-graph.sh [--root DIR] [--out DIR] [--no-build]
#
# The viewer is a single file with the data inlined, so it opens over file://
# with no local web server — nothing is left running after you close the tab.
set -eu

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT="${LLM_WIKI_ROOT:-$HOME/llm-wiki-docs}"
OUT=""
BUILD=1

while [ $# -gt 0 ]; do
  case "$1" in
    --root) ROOT="${2:?--root needs a directory}"; shift 2 ;;
    --out)  OUT="${2:?--out needs a directory}"; shift 2 ;;
    --no-build) BUILD=0; shift ;;
    -h|--help) echo "usage: open-graph.sh [--root DIR] [--out DIR] [--no-build]"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 64 ;;
  esac
done

[ -n "$OUT" ] || OUT="$ROOT/.graph"

if [ "$BUILD" = 1 ]; then
  PY=""
  for p in ${KL_PY-python3 python}; do
    command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }
  done
  [ -n "$PY" ] || { echo "python3 not found — cannot build the graph" >&2; exit 1; }
  "$PY" "$HERE/build_graph.py" --root "$ROOT" --out "$OUT"
fi

HTML="$OUT/graph.html"
[ -f "$HTML" ] || { echo "no graph yet at $HTML — run without --no-build" >&2; exit 1; }

# Platform opener. If none fits, print the path: the user can open it by hand.
if command -v open >/dev/null 2>&1; then
  open "$HTML"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$HTML" >/dev/null 2>&1 &
elif command -v wslview >/dev/null 2>&1; then
  wslview "$HTML"
elif command -v cmd.exe >/dev/null 2>&1; then
  cmd.exe /c start "" "$(wslpath -w "$HTML" 2>/dev/null || echo "$HTML")"
else
  echo "no browser opener found. open this file yourself:"
fi
echo "$HTML"
