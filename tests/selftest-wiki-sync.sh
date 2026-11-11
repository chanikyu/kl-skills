#!/bin/sh
# Checks the Stop gate that catches pages written outside Write/Edit.
#
# The thing worth testing is not "does it run" but "does it notice a change it
# never saw happen". So the fixture changes a page with plain shell — the exact
# path that made the PostToolUse gates useless — and the gate must still react.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — wiki-sync selftest skipped"
  exit 0
fi

mkdir -p "$TMP/t/wiki"
printf '# Page\n\ncross-mapping 위험은 낮다. 관련 [[ghost]].\n' > "$TMP/t/wiki/page.md"
printf '# t — index\n'                                        > "$TMP/t/wiki/index.md"
printf '# t — log\n'                                          > "$TMP/t/wiki/log.md"

export LLM_WIKI_ROOT="$TMP"
sync() { printf '%s' "${1:-{\}}" | sh "$REPO/hooks/run.sh" wiki-sync 2>/dev/null; }

# --- 그래프가 아직 없다: 전부 바뀐 것으로 보고 만들어야 한다
out="$(sync)"
[ -f "$TMP/.graph/graph.json" ] && ok "그래프 db 를 만들었다" || bad "그래프 db 가 없다"
case "$out" in
  *"graph built"*) ok "무엇을 했는지 보고한다" ;;
  *)               bad "보고가 없다: $out" ;;
esac
case "$out" in
  *undefined-term*) ok "바뀐 페이지의 글을 검사했다" ;;
  *)                bad "글 검사 결과가 없다: $out" ;;
esac

# --- 바뀐 게 없으면 조용해야 한다. 세션마다 떠들면 보고가 아니라 잡음이다
out="$(sync)"
[ -z "$out" ] && ok "바뀐 게 없으면 아무 말도 안 한다" || bad "안 바뀌었는데 말했다: $out"

# --- 쉘로 페이지를 고친다. PostToolUse 가 절대 못 보는 경로다
printf '\n한 줄 더. taxon 이라는 말도 쓴다.\n' >> "$TMP/t/wiki/page.md"
out="$(sync)"
case "$out" in
  *"graph built"*) ok "Write/Edit 아닌 경로로 바뀐 것도 잡는다" ;;
  *)               bad "쉘로 바뀐 페이지를 못 잡았다: $out" ;;
esac
case "$out" in
  *"'taxon'"*) ok "새로 들어온 용어를 지적한다" ;;
  *)           bad "새 용어를 못 잡았다" ;;
esac

# --- 목차와 기록은 한 줄 목록이다. 글 규칙 대상이 아니다
printf '\n- [page](page.md) — 한 줄\n' >> "$TMP/t/wiki/index.md"
out="$(sync)"
[ -z "$out" ] && ok "index.md 만 바뀌면 조용하다" || bad "index.md 를 페이지로 셌다: $out"

# --- 위키가 없는 컴퓨터에서도 조용히 끝나야 한다
out="$(LLM_WIKI_ROOT="$TMP/nope" sync)"
[ -z "$out" ] && ok "위키 뿌리가 없으면 조용하다" || bad "위키가 없는데 말했다: $out"

# --- 훅은 무슨 입력이 와도 세션을 깨지 않는다
sync 'not json' >/dev/null 2>&1 && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"
sync '' >/dev/null 2>&1 && ok "빈 입력에도 0으로 끝난다" || bad "빈 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all wiki-sync checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
