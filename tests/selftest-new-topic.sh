#!/bin/sh
# Checks new-topic.sh: it must create the files a wiki cannot work without,
# must not overwrite them on a second run, and must refuse a topic that is a path.
set -u

S="$(CDPATH= cd -- "$(dirname -- "$0")/../skills/llm-wiki-docs/scripts" && pwd)/new-topic.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export LLM_WIKI_ROOT="$TMP"
fails=0

ok()   { echo "ok    $1"; }
bad()  { echo "FAIL  $1"; fails=$((fails + 1)); }

# --- first run creates the layout
sh "$S" demo-topic "a demo" >/dev/null 2>&1 || bad "first run exited non-zero"
for f in README.md wiki/index.md wiki/log.md raw/.gitkeep; do
  [ -e "$TMP/demo-topic/$f" ] && ok "created $f" || bad "missing $f"
done

# --- the description reaches README, so the topic says what it is
grep -q "a demo" "$TMP/demo-topic/README.md" && ok "description written into README" \
  || bad "description missing from README"

# --- re-running must not clobber work already in the wiki
echo "EDITED BY HAND" >> "$TMP/demo-topic/wiki/index.md"
sh "$S" demo-topic >/dev/null 2>&1 || bad "second run exited non-zero"
grep -q "EDITED BY HAND" "$TMP/demo-topic/wiki/index.md" \
  && ok "second run preserved existing index.md" \
  || bad "second run overwrote index.md — data loss"

# --- a missing file is refilled without touching the others
rm "$TMP/demo-topic/wiki/log.md"
sh "$S" demo-topic >/dev/null 2>&1
[ -e "$TMP/demo-topic/wiki/log.md" ] && ok "refilled a deleted log.md" || bad "did not refill log.md"
grep -q "EDITED BY HAND" "$TMP/demo-topic/wiki/index.md" \
  && ok "refill left index.md alone" || bad "refill clobbered index.md"

# --- reject input that would write outside the root
for bogus in "../escape" "a/b" "" "-rf"; do
  if sh "$S" "$bogus" >/dev/null 2>&1; then
    bad "accepted bad topic '$bogus'"
  else
    ok "rejected bad topic '${bogus:-<empty>}'"
  fi
done
[ -e "$TMP/escape" ] && bad "wrote outside the root" || ok "nothing written outside the root"

[ "$fails" -eq 0 ] || { echo "$fails check(s) failed"; exit 1; }
echo "all checks passed"
