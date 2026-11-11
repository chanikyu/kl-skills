#!/bin/sh
# Checks index-add.py, log-append.py and lint.py: the index must never grow a
# second line for one page, the log must only ever gain lines at the bottom, and
# each lint check must fire on the case it is for.
set -u

S="$(CDPATH= cd -- "$(dirname -- "$0")/../skills/llm-wiki-docs/scripts" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export LLM_WIKI_ROOT="$TMP"
fails=0
ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

IDX="$TMP/t/wiki/index.md"
LOG="$TMP/t/wiki/log.md"
sh "$S/new-topic.sh" t "test topic" >/dev/null 2>&1
printf '# A\n\nlinks to [[b]] and [[ghost]].\n' > "$TMP/t/wiki/a.md"
printf '# B\n\nno links.\n'                     > "$TMP/t/wiki/b.md"

# --- index-add: one page must never end up with two lines
python3 "$S/index-add.py" t a.md Concepts "first"  >/dev/null
python3 "$S/index-add.py" t a.md Concepts "second" >/dev/null
python3 "$S/index-add.py" t a.md Entities "moved"  >/dev/null
n="$(grep -c '(a\.md)' "$IDX")"
[ "$n" = "1" ] && ok "index holds exactly one line per page after update+move" \
  || bad "index has $n lines for a.md, want 1"
grep -q 'moved' "$IDX" && ok "the surviving line is the newest one" || bad "stale summary survived"
grep -q '^## Entities' "$IDX" && ok "missing category section is created" || bad "no Entities section"

# --- a section emptied by a move must not be left looking like it has content
awk '/^## Concepts/{f=1;next} /^## /{f=0} f&&NF{print}' "$IDX" | grep -q 'nothing yet' \
  && ok "emptied section gets its placeholder back" || bad "emptied section left bare"

# --- a second run with identical input must not touch the file
cp "$IDX" "$TMP/idx.before"
python3 "$S/index-add.py" t a.md Entities "moved" >/dev/null
cmp -s "$IDX" "$TMP/idx.before" && ok "re-adding identical entry changes nothing" \
  || bad "identical re-add rewrote the index"

# --- index.md and log.md are machinery, not pages
python3 "$S/index-add.py" t index.md Concepts "x" >/dev/null 2>&1 \
  && bad "accepted index.md as a page" || ok "refuses to index index.md"

# --- log-append: only ever adds at the bottom
python3 "$S/index-add.py" t b.md Entities "b page" >/dev/null
cp "$LOG" "$TMP/log.before"
before="$(wc -l < "$TMP/log.before")"
python3 "$S/log-append.py" t ingest "a source" --pages a.md --note "n" >/dev/null
after="$(wc -l < "$LOG")"
[ "$after" -gt "$before" ] && ok "log gained lines" || bad "log did not grow"
# Compare by line count, not bytes: the file can be shorter than any byte window,
# in which case the window would reach into the newly appended text.
head -n "$before" "$LOG" | cmp -s - "$TMP/log.before" \
  && ok "log history untouched (append-only)" || bad "log rewrote earlier content"
tail -4 "$LOG" | grep -qE '^## \[[0-9]{4}-[0-9]{2}-[0-9]{2}\] ingest \| a source$' \
  && ok "log entry uses the grep-able prefix" || bad "log prefix format wrong"
python3 "$S/log-append.py" t gossip "x" >/dev/null 2>&1 \
  && bad "accepted an operation outside ingest/query/lint" || ok "rejects unknown operation"

# --- lint: each check fires on its own case
out="$(python3 "$S/lint.py" t 2>&1)"
echo "$out" | grep -q 'broken-link .*ghost' && ok "lint finds a link to a missing page" \
  || bad "lint missed broken-link"
echo "$out" | grep -q 'orphan .*a\.md' && ok "lint finds the page nothing links to" \
  || bad "lint missed orphan"
echo "$out" | grep -q 'orphan .*b\.md' && bad "b.md is linked from a.md, not an orphan" \
  || ok "a linked page is not reported as orphan"

printf '# Ghost page\n' > "$TMP/t/wiki/ghost.md"
python3 "$S/index-add.py" t ghost.md Concepts "now real" >/dev/null
rm "$TMP/t/wiki/b.md"
out="$(python3 "$S/lint.py" t 2>&1)"
echo "$out" | grep -q 'dangling-index .*b\.md' && ok "lint finds an index entry with no file" \
  || bad "lint missed dangling-index"
printf '# Loose\n' > "$TMP/t/wiki/loose.md"
out="$(python3 "$S/lint.py" t 2>&1)"
echo "$out" | grep -q 'not-indexed .*loose\.md' && ok "lint finds a page missing from the index" \
  || bad "lint missed not-indexed"
# loose.md was never logged; a.md was logged above. The pair proves the check reads
# the log, not the index. (b.md is gone by now — the dangling-index case deleted it.)
echo "$out" | grep -q 'not-logged .*loose\.md' && ok "lint finds a page the log never mentions" \
  || bad "lint missed not-logged"
echo "$out" | grep -q 'not-logged .*a\.md' && bad "a.md is in the log, not a finding" \
  || ok "a logged page is not reported as not-logged"
printf '%s\n' '- [loose](loose.md) — dup' >> "$IDX"
printf '%s\n' '- [loose](loose.md) — dup' >> "$IDX"
out="$(python3 "$S/lint.py" t 2>&1)"
echo "$out" | grep -q 'duplicate-index .*loose\.md' && ok "lint finds a page listed twice" \
  || bad "lint missed duplicate-index"

# --- a clean wiki must exit 0, and overview.md must not count as an orphan
sh "$S/new-topic.sh" clean "clean topic" >/dev/null 2>&1
printf '# Overview\n\nentry point.\n' > "$TMP/clean/wiki/overview.md"
python3 "$S/index-add.py" clean overview.md Overview "entry point" >/dev/null
# Indexed is not enough any more: a page the log never mentions is also a finding.
python3 "$S/lint.py" clean >/dev/null 2>&1
[ $? -eq 1 ] && ok "indexed but never logged is still a finding" \
  || bad "not-logged did not fire for an unlogged page"
python3 "$S/log-append.py" clean ingest "overview written" --pages overview.md >/dev/null
python3 "$S/lint.py" clean >/dev/null 2>&1
[ $? -eq 0 ] && ok "indexed + logged wiki exits 0, overview.md is orphan-exempt" \
  || bad "clean wiki reported findings"

# --- a topic that does not exist must say so, with the fix
out="$(python3 "$S/lint.py" nope 2>&1)"
echo "$out" | grep -q 'new-topic.sh nope' && ok "unknown topic names the command that fixes it" \
  || bad "unhelpful error for unknown topic: $out"

[ "$fails" -eq 0 ] || { echo "$fails check(s) failed"; exit 1; }
echo "all checks passed"
