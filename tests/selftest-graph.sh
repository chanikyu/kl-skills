#!/bin/sh
# Checks the graph build and the hook gate that triggers it.
#
# The parsing rules are the part that can be silently wrong — a link counted from
# inside a code fence, or a raw/ source counted as a page, changes the picture
# without erroring. So the fixture below contains one of each edge case and the
# test asserts the exact node and link counts.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BUILD="$REPO/skills/graph-doc-memory/scripts/build_graph.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
G="$TMP/.graph/graph.json"
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 on this machine — graph selftest skipped"
  exit 0
fi

# --- fixture: two topics, every link form, plus things that must NOT become nodes
mkdir -p "$TMP/topic-a/wiki" "$TMP/topic-a/raw" "$TMP/topic-b/wiki"

echo '# topic-a readme with a [[readme-link]]' > "$TMP/topic-a/README.md"
echo '# a raw source with a [[raw-link]]' > "$TMP/topic-a/raw/source.md"

cat > "$TMP/topic-a/wiki/index.md" <<'EOF'
# topic-a — index
- [a-one](a-one.md) — markdown link form
- [[a-two]] — wikilink form
EOF

cat > "$TMP/topic-a/wiki/a-one.md" <<'EOF'
# Page A One
Links to [[a-two|an alias]] and [[a-two#a-heading]] (same target twice: counts once).
Points at [[not-written-yet]], which does not exist.

```markdown
[[fenced-example]] must not count
```

Inline `[[inline-example]]` must not count either.
An external [link](https://example.com/page.md) is not a wiki link.
EOF

cat > "$TMP/topic-a/wiki/a-two.md" <<'EOF'
# Page A Two
Explicit cross-topic link: [[topic-b/b-one]].
EOF

cat > "$TMP/topic-b/wiki/b-one.md" <<'EOF'
# Page B One
Bare name that exists in exactly one other topic: [[a-one]].
EOF

echo '# An orphan with no links at all' > "$TMP/topic-b/wiki/orphan.md"

# --- build
"$PY" "$BUILD" --root "$TMP" >"$TMP/build.out" 2>&1 \
  && ok "build exited 0" || { bad "build failed: $(cat "$TMP/build.out")"; exit 1; }
[ -f "$G" ] && ok "graph.json written" || bad "graph.json missing"
[ -f "$TMP/.graph/graph.html" ] && ok "graph.html written" || bad "graph.html missing"

q() { "$PY" -c "import json;g=json.load(open('$G'));print($1)"; }

check() { # check <label> <expr> <expected>
  got="$(q "$2")"
  [ "$got" = "$3" ] && ok "$1 = $3" || bad "$1: expected $3, got $got"
}

check "pages"   "g['stats']['pages']"   5
check "nodes"   "g['stats']['nodes']"   6
check "links"   "g['stats']['links']"   6
check "missing" "g['stats']['missing']" 1
check "orphans" "g['stats']['orphans']" 1
check "topics"  "g['stats']['topics']"  2

ids="$(q "' '.join(n['id'] for n in g['nodes'])")"
for want in topic-a/index topic-a/a-one topic-a/a-two topic-b/b-one topic-b/orphan topic-a/not-written-yet; do
  case " $ids " in *" $want "*) ok "node present: $want" ;; *) bad "node missing: $want" ;; esac
done
for unwanted in fenced-example inline-example raw-link readme-link source example.com; do
  case "$ids" in *"$unwanted"*) bad "node must not exist: $unwanted" ;; *) ok "excluded: $unwanted" ;; esac
done

edges="$(q "' '.join(l['source']+'>'+l['target'] for l in g['links'])")"
for want in "topic-a/index>topic-a/a-one" "topic-a/index>topic-a/a-two" \
            "topic-a/a-one>topic-a/a-two" "topic-a/a-one>topic-a/not-written-yet" \
            "topic-a/a-two>topic-b/b-one" "topic-b/b-one>topic-a/a-one"; do
  case " $edges " in *" $want "*) ok "edge: $want" ;; *) bad "edge missing: $want" ;; esac
done

check "a-two inbound degree" "[n['in'] for n in g['nodes'] if n['id']=='topic-a/a-two'][0]" 2
check "missing page marked"  "[n['exists'] for n in g['nodes'] if n['id']=='topic-a/not-written-yet'][0]" False
check "title from heading"   "[n['title'] for n in g['nodes'] if n['id']=='topic-a/a-one'][0]" "Page A One"

# --- the viewer must carry the data, with no placeholder left behind
grep -q "__GRAPH_DATA__" "$TMP/.graph/graph.html" \
  && bad "graph.html still has the __GRAPH_DATA__ placeholder" \
  || ok "placeholder replaced"
grep -q "topic-a/a-one" "$TMP/.graph/graph.html" \
  && ok "graph.html carries the inlined data" || bad "graph.html has no data"

# --- hook gate: a wiki page triggers a rebuild
export LLM_WIKI_ROOT="$TMP"
hook() { printf '%s' "$1" | sh "$REPO/hooks/run.sh" wiki-graph 2>/dev/null; }

rm -f "$G"
out="$(hook "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$TMP/topic-a/wiki/a-one.md\"}}")"
[ -f "$G" ] && ok "hook rebuilt the graph for a wiki page" || bad "hook did not rebuild"
case "$out" in *"graph built"*) ok "hook reported the rebuild" ;; *) bad "hook said nothing: '$out'" ;; esac

# --- anything outside the wiki must be ignored, silently
rm -f "$G"
out="$(hook "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$TMP/topic-a/raw/source.md\"}}")"
[ -f "$G" ] && bad "rebuilt for a raw/ file" || ok "ignored a raw/ file"
out="$(hook '{"tool_name":"Write","tool_input":{"file_path":"/tmp/elsewhere.md"}}')"
[ -f "$G" ] && bad "rebuilt for a file outside the wiki root" || ok "ignored a file outside the root"
[ -z "$out" ] && ok "stayed silent for unrelated edits" || bad "printed for an unrelated edit: '$out'"

# --- a hook must never break a session, whatever arrives on stdin
hook 'not json at all' >/dev/null 2>&1 && ok "survived malformed payload" || bad "malformed payload exited non-zero"
hook '' >/dev/null 2>&1 && ok "survived empty payload" || bad "empty payload exited non-zero"

# --- does the viewer actually draw? A thrown exception leaves a blank graph with no
# --- error anywhere, which is how two real bugs got in. So render it headless and
# --- count what came out. Skipped when no Chrome is installed (CI without a browser).
CHROME=""
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "/Applications/Chromium.app/Contents/MacOS/Chromium" \
         google-chrome chromium chromium-browser; do
  if [ -x "$c" ] || command -v "$c" >/dev/null 2>&1; then CHROME="$c"; break; fi
done

if [ -z "$CHROME" ]; then
  echo "skip  no chrome/chromium — viewer render check skipped"
else
  "$PY" "$BUILD" --root "$TMP" --quiet
  PROBE="$TMP/.graph/probe.html"
  # The probe drives the controls the way a user would and reports through <title>,
  # because --dump-dom is the only channel out of headless chrome without a driver.
  "$PY" - "$TMP/.graph/graph.html" "$PROBE" <<'PROBEEOF'
import sys
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding="utf-8").read()
probe = """
<script>
addEventListener('load', () => setTimeout(() => {
  const t = s => document.title = 'PROBE ' + s;
  if (typeof d3 === 'undefined') return t('NO-D3');
  try {
    const n = () => document.querySelectorAll('.nodes circle').length;
    const fire = (el, ev) => el.dispatchEvent(new Event(ev, {bubbles: true}));
    const all = n();
    const orphan = document.getElementById('fOrphan');
    orphan.checked = false; fire(orphan, 'change');
    const noOrphan = n();
    orphan.checked = true; fire(orphan, 'change');
    const miss = document.getElementById('fMissing');
    miss.checked = false; fire(miss, 'change');
    const noMissing = n();
    miss.checked = true; fire(miss, 'change');
    const q = document.getElementById('q');
    q.value = 'a-one'; fire(q, 'input');
    const searched = n();
    q.value = ''; fire(q, 'input');
    document.querySelector('.nodes circle').dispatchEvent(new MouseEvent('click', {bubbles: true}));
    const detail = document.querySelectorAll('#detail .t').length;
    document.getElementById('repel').value = 900; fire(document.getElementById('repel'), 'input');
    document.getElementById('reset').click();
    t(`all=${all} noOrphan=${noOrphan} noMissing=${noMissing} searched=${searched} detail=${detail} after=${n()}`);
  } catch (e) { t('ERROR ' + e.message); }
}, 400));
</script>
</body>"""
open(dst, "w", encoding="utf-8").write(h.replace("</body>", probe, 1))
PROBEEOF
  "$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=9000 \
    --user-data-dir="$TMP/chrome-profile" --dump-dom "file://$PROBE" \
    >"$TMP/dom.html" 2>"$TMP/chrome.log" || true

  # -o, not -c: the dumped DOM is a single line, so -c would always report 1.
  circles=$(grep -o '<circle' "$TMP/dom.html" 2>/dev/null | wc -l | tr -d ' ')
  title=$("$PY" -c "import re,sys;h=open('$TMP/dom.html',encoding='utf-8',errors='replace').read();m=re.search(r'<title>([^<]*)</title>',h);print((m.group(1) if m else 'none').strip())")

  case "$title" in
    "PROBE NO-D3")
      echo "skip  d3 CDN unreachable — viewer render check skipped" ;;
    "PROBE ERROR"*)
      bad "viewer threw while being driven: $title" ;;
    "PROBE all=6 noOrphan=5 noMissing=5 searched=1 detail=1 after=6")
      ok "viewer renders and every control responds ($title)" ;;
    "PROBE "*)
      bad "viewer drew the wrong thing: $title" ;;
    *)
      bad "viewer never finished loading (title: $title)" ;;
  esac
  [ "$circles" -gt 0 ] && ok "viewer drew $circles nodes" || bad "viewer drew no nodes at all"
fi

echo
if [ "$fails" -eq 0 ]; then
  echo "all graph checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
