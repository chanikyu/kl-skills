#!/bin/sh
# Checks wiki-recall: the right page must come first, an unrelated question must
# get nothing, and the hook must stay silent unless something is clearly related.
# The silent cases matter as much as the hits — this hook runs on every message,
# and a hook that attaches a wrong page every time gets switched off.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
RECALL="$REPO/skills/wiki-recall/scripts/recall.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — wiki-recall selftest skipped"
  exit 0
fi

mkdir -p "$TMP/harness/wiki" "$TMP/cooking/wiki"
cat > "$TMP/harness/wiki/plugin-update.md" <<'EOF'
# 플러그인 업데이트 함정

플러그인을 업데이트해도 세션을 다시 시작해야 훅이 바뀐다. 훅은 세션이 시작될 때 읽힌다.
EOF
cat > "$TMP/harness/wiki/graph-view.md" <<'EOF'
# 그래프 뷰

로컬 그래프는 깊이 슬라이더로 몇 다리까지 보여줄지 정한다. 관련: [[plugin-update]]
EOF
cat > "$TMP/cooking/wiki/kimchi-stew.md" <<'EOF'
# 김치찌개

돼지고기와 김치를 먼저 볶은 뒤 물을 붓는다.
EOF
printf '# harness — index\n\n- [plugin-update](plugin-update.md) — 플러그인 업데이트 훅\n' > "$TMP/harness/wiki/index.md"
printf '# harness — log\n\n## [2026-11-11] ingest | 플러그인 업데이트 훅\n' > "$TMP/harness/wiki/log.md"
export LLM_WIKI_ROOT="$TMP"

# --- 맞는 페이지가 먼저 나온다 (조사가 붙은 질문으로)
out="$("$PY" "$RECALL" "플러그인을 업데이트했는데 훅이 그대로야" --mode rag 2>&1)"
first="$(printf '%s\n' "$out" | grep '^- ' | head -1)"
case "$first" in *plugin-update.md*) ok "관련 페이지가 1위로 나온다" ;; *) bad "1위가 틀렸다: $first" ;; esac
case "$out" in *index.md*|*log.md*) bad "목차·기록을 검색 결과에 넣었다" ;; *) ok "목차와 기록은 검색하지 않는다" ;; esac

# --- 위키가 모르는 질문에는 아무것도 주지 않는다
out="$("$PY" "$RECALL" "주식 시장 전망 알려줘" --mode rag --min-coverage 0.4 2>&1)"; code=$?
[ -z "$out" ] && [ "$code" -ne 0 ] && ok "관련 없는 질문에는 아무것도 주지 않는다" || bad "무관한 질문에 결과가 나왔다: $out"
out="$("$PY" "$RECALL" "다음에 뭘 할까" --mode rag --min-coverage 0.4 2>&1)"
[ -z "$out" ] && ok "흔한 낱말뿐인 질문에도 주지 않는다" || bad "흔한 낱말로 결과가 나왔다: $out"

# --- 위키 크기에 따라 CAG 와 RAG 를 고른다
out="$("$PY" "$RECALL" "그래프 깊이" 2>&1)"
case "$out" in *"CAG"*) ok "작은 위키는 통째로 가져온다 (CAG)" ;; *) bad "작은 위키인데 CAG 가 아니다: $out" ;; esac
count="$(printf '%s\n' "$out" | grep -c '^- ')"
[ "$count" -eq 3 ] && ok "CAG 는 페이지 전부(3장)를 준다" || bad "CAG 페이지 수: $count"
out="$("$PY" "$RECALL" "그래프 깊이" --cag-max-chars 10 2>&1)"
case "$out" in *"RAG"*) ok "기준보다 크면 골라서 가져온다 (RAG)" ;; *) bad "큰 위키인데 RAG 가 아니다: $out" ;; esac
out="$("$PY" "$RECALL" "그래프 깊이 슬라이더" --mode rag --full 2>&1)"
case "$out" in *"===== "*"몇 다리까지"*) ok "--full 이면 본문 전체를 붙인다" ;; *) bad "--full 인데 본문이 없다" ;; esac

# --- 그래프가 있으면 링크로 이어진 이웃도 붙는다
"$PY" "$REPO/skills/graph-doc-memory/scripts/build_graph.py" --root "$TMP" --quiet
out="$("$PY" "$RECALL" "로컬 그래프 깊이 슬라이더" --mode rag --min-coverage 0.4 2>&1)"
case "$out" in *"링크로 이어진"*plugin-update.md*|*plugin-update.md*"링크로 이어진"*) ok "링크로 이어진 이웃 페이지를 같이 준다" ;; *) bad "이웃을 못 붙였다: $out" ;; esac

# --- 훅: 관련이 분명할 때만, 모델에게 닿는 모양으로 붙인다
export CLAUDE_PLUGIN_ROOT="$REPO"
prompt_hook() { printf '%s' "$1" | sh "$REPO/hooks/run.sh" wiki-recall 2>/dev/null; }
out="$(prompt_hook '{"prompt":"플러그인을 업데이트했는데 훅이 그대로야, 왜 그래?"}')"
printf '%s' "$out" | "$PY" -c "import json,sys; d=json.load(sys.stdin)['hookSpecificOutput']; assert d['hookEventName']=='UserPromptSubmit'; assert 'plugin-update.md' in d['additionalContext']" 2>/dev/null \
  && ok "관련 있는 메시지에 위키 페이지를 붙인다 (UserPromptSubmit JSON)" \
  || bad "관련 메시지인데 안 붙였거나 JSON 이 아니다: $out"
out="$(prompt_hook '{"prompt":"그래"}')"
[ -z "$out" ] && ok "짧은 말에는 조용하다" || bad "짧은 말에 붙였다: $out"
out="$(prompt_hook '{"prompt":"오늘 저녁 메뉴는 무엇으로 할지 고민이다"}')"
[ -z "$out" ] && ok "위키와 무관한 메시지에는 조용하다" || bad "무관한 메시지에 붙였다: $out"
out="$(prompt_hook '{"prompt":"/clear 하고 다시 시작"}')"
[ -z "$out" ] && ok "/ 명령에는 조용하다" || bad "명령에 붙였다: $out"
printf 'not json' | sh "$REPO/hooks/run.sh" wiki-recall >/dev/null 2>&1 \
  && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all wiki-recall checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
