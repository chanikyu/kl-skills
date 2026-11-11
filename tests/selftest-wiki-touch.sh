#!/bin/sh
# Checks the Bash gate: a wiki page written by a shell command must still be noticed.
#
# This one needs the compiled binary, because the gate is Rust — the matcher fires
# on every Bash call, where a 32 ms interpreter start would be felt. When the local
# binary predates the gate, the checks are skipped rather than reported as failures.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

T="$(sh "$REPO/hooks/run.sh" --print-target)"
BIN="$REPO/bin/kl-gate-$T"
if [ -z "$T" ] || [ ! -x "$BIN" ]; then
  echo "skip  no binary for this machine — wiki-touch selftest skipped"
  exit 0
fi
if ! grep -q "wiki-touch" "$BIN" 2>/dev/null; then
  echo "skip  the local binary predates wiki-touch — rebuild via CI, then rerun"
  exit 0
fi
PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — the gate would have nothing to hand the work to"
  exit 0
fi

mkdir -p "$TMP/t/wiki"
printf '# Page\n\ncross-mapping 위험은 낮다.\n' > "$TMP/t/wiki/page.md"
printf '# t — index\n'                        > "$TMP/t/wiki/index.md"
printf '# t — log\n'                          > "$TMP/t/wiki/log.md"

export LLM_WIKI_ROOT="$TMP"
export CLAUDE_PLUGIN_ROOT="$REPO"
touch_gate() { printf '{}' | sh "$REPO/hooks/run.sh" wiki-touch 2>/dev/null; }

# --- 그래프가 아직 없다: 밀려 있으므로 맞춰야 한다
out="$(touch_gate)"
case "$out" in
  *"graph built"*) ok "그래프가 없으면 만든다" ;;
  *)               bad "아무 일도 하지 않았다: $out" ;;
esac
[ -f "$TMP/.graph/graph.json" ] && ok "그래프 db 가 생겼다" || bad "그래프 db 가 없다"

# --- 두 번째 호출은 조용해야 한다. Bash 호출마다 떠들면 쓸 수 없다
out="$(touch_gate)"
[ -z "$out" ] && ok "바뀐 게 없으면 아무 말도 안 한다" || bad "안 바뀌었는데 말했다: $out"

# --- 쉘로 페이지를 고친다. 이 게이트가 존재하는 이유다
printf '\ntaxon 이라는 말을 새로 쓴다.\n' >> "$TMP/t/wiki/page.md"
out="$(touch_gate)"
case "$out" in
  *"graph built"*) ok "쉘로 고친 페이지를 잡는다" ;;
  *)               bad "쉘 수정을 놓쳤다: $out" ;;
esac
case "$out" in
  *"'taxon'"*) ok "글 검사까지 이어진다" ;;
  *)           bad "글 검사 결과가 없다" ;;
esac

# --- 목차·기록만 바뀌면 조용하다 (파일을 쓸 때마다 도는 게이트라 특히 중요하다)
printf '\n- [page](page.md) — 한 줄\n' >> "$TMP/t/wiki/index.md"
out="$(touch_gate)"
[ -z "$out" ] && ok "목차만 바뀌면 조용하다" || bad "목차를 페이지로 셌다: $out"

# --- 위키가 없는 컴퓨터
out="$(LLM_WIKI_ROOT="$TMP/nope" touch_gate)"
[ -z "$out" ] && ok "위키 뿌리가 없으면 조용하다" || bad "위키가 없는데 말했다: $out"

# --- 세션을 깨지 않는다
printf 'not json' | sh "$REPO/hooks/run.sh" wiki-touch >/dev/null 2>&1 \
  && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all wiki-touch checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
