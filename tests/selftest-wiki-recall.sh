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
# 작업 끝 알림은 사람이 쓴 메시지가 아니다 (2026-11-13: 알림 글로 위키·스킬을 찾았다)
out="$(prompt_hook '{"prompt":"<task-notification>\n<summary>플러그인을 업데이트했는데 훅이 그대로야</summary>\n</task-notification>"}')"
[ -z "$out" ] && ok "작업 알림에는 조용하다" || bad "작업 알림에 위키를 붙였다: $out"
out="$(prompt_hook '{"prompt":"/clear 하고 다시 시작"}')"
[ -z "$out" ] && ok "/ 명령에는 조용하다" || bad "명령에 붙였다: $out"
# --- 2026-11-11 오탐: 한 글자 낱말('손', '위')을 다른 낱말 속("손상", "무작위")에서 찾아
#     관련 없는 페이지를 "질문을 60% 덮음" 으로 붙였다. hook-replay 로 세션 전체에서 3번 재현됐다.
mkdir -p "$TMP/biology/wiki"
cat > "$TMP/biology/wiki/dysbiosis.md" <<'PAGE'
# 장내 미생물

세균이 다시 뇌 손상을 키웠다. 무작위 시험을 같이 봐야 한다. 세균이 하나도 없는 쥐다. 아직 몇 개뿐인 것이다.
PAGE
out="$(prompt_hook '{"prompt":"위 3개 스킬 진행하고 먼저 손 봐야 하는 것도 진행해줘."}')"
[ -z "$out" ] && ok "한 글자 낱말을 다른 낱말 속에서 찾지 않는다" || bad "낱말 속 글자로 무관한 페이지를 붙였다: $out"
"$PY" - "$RECALL" <<'PYCHECK' && ok "홀로 선 한 글자 낱말(조사가 붙어도)은 찾는다" || bad "홀로 선 한 글자 낱말을 못 찾는다"
import importlib.util, sys
spec = importlib.util.spec_from_file_location("recall", sys.argv[1])
recall = importlib.util.module_from_spec(spec); spec.loader.exec_module(recall)
assert recall.page_has_word(set(), "손을 자주 씻는다", "손")
assert recall.page_has_word(set(), "훅 하나가 돈다", "훅")
assert not recall.page_has_word(set(), "뇌 손상을 키웠다", "손")
assert not recall.page_has_word(set(), "무작위 시험", "위")
PYCHECK
# --- 2026-11-20: "Tauri를" 의 '를' 과 "뭐였지" 같은 풀이말이 질문 낱말로 남아, 위키에 없다는
#     이유로 가장 큰 무게를 받고 맞는 페이지의 덮는 비율을 28% 로 깎았다
"$PY" - "$RECALL" <<'PYCHECK' && ok "조사만 남은 덩어리와 풀이말은 질문 낱말에서 뺀다" || bad "조사·풀이말이 질문 낱말에 남는다"
import importlib.util, sys
spec = importlib.util.spec_from_file_location("recall", sys.argv[1])
recall = importlib.util.module_from_spec(spec); spec.loader.exec_module(recall)
stop, particles = recall.load_stop_tokens(), recall.load_word_list("particles.txt")
words = recall.query_words("Tauri를 고른 이유가 뭐였지?", stop, particles)
assert words == {"tauri", "고른", "이유"}, words
assert recall.query_words("API가 바뀔까 할까", stop, particles) == {"api"}
# 이름씨 + 이었/였 은 이름씨를 남긴다
assert "방식" in recall.query_words("무슨 방식이었지", stop, particles)
assert recall.is_predicate("정했지") and recall.is_predicate("있을까")
assert not recall.is_predicate("이미지") and not recall.is_predicate("메시지")
PYCHECK
# --- 목차의 한 줄 설명으로도 찾는다. 본문에 없는 말("바이너리", "굳는")이 설명에만 있다
mkdir -p "$TMP/summary/release/wiki"
printf '# 배포 순서\n\nCI 가 끝난 뒤에 설치한다.\n' > "$TMP/summary/release/wiki/order.md"
printf '# 버전 번호\n\n고치기만 했으면 끝자리를 올린다.\n' > "$TMP/summary/release/wiki/version.md"
printf '# release — index\n\n- [order](order.md) — 옛 바이너리가 설치본에 굳는 것을 막는 순서\n' > "$TMP/summary/release/wiki/index.md"
out="$("$PY" "$RECALL" "설치본에 바이너리가 굳는 순서" --root "$TMP/summary" --mode rag --min-coverage 0.4 2>&1)"
first="$(printf '%s\n' "$out" | grep '^- ' | head -1)"
case "$first" in *order.md*) ok "목차의 한 줄 설명으로도 페이지를 찾는다" ;; *) bad "목차 설명으로 못 찾았다: $out" ;; esac
# --- 2026-11-20: 덮는 비율을 페이지 전체로 재면, 긴 페이지는 질문 낱말이 서로 다른 문단에
#     흩어져 있어도 기준을 넘었다(실제 메시지 1,163개 중 533개에 붙음). 한 덩어리 안에서 잰다
mkdir -p "$TMP/chunk/notes/wiki"
printf '# 장보기 기록\n\n딸기를 샀다.\n\n수박을 깎았다.\n\n자두는 비쌌다.\n' > "$TMP/chunk/notes/wiki/diary.md"
printf '# 과일 가게\n\n딸기와 수박을 같이 판다.\n' > "$TMP/chunk/notes/wiki/shop.md"
printf '# 날씨\n\n오늘은 맑다.\n' > "$TMP/chunk/notes/wiki/weather.md"
out="$("$PY" "$RECALL" "딸기 수박" --root "$TMP/chunk" --mode rag --min-coverage 0.4 2>&1)"
case "$out" in *shop.md*) ok "질문 낱말이 한 문단에 함께 있는 페이지는 붙인다" ;; *) bad "한 문단에 함께 있는데 못 찾았다: $out" ;; esac
case "$out" in *diary.md*) bad "낱말이 다른 문단에 흩어진 페이지를 붙였다: $out" ;; *) ok "낱말이 다른 문단에 흩어진 페이지는 붙이지 않는다" ;; esac
# --- 작업 폴더를 주면 다른 프로젝트의 주제는 붙이지 않는다. 이름을 말하거나 공용 주제면 붙인다
mkdir -p "$TMP/proj/alpha/wiki" "$TMP/proj/beta/wiki" "$TMP/proj/gamma/wiki"
printf '# 배포 순서\n\nCI 가 끝난 뒤에 설치한다.\n' > "$TMP/proj/alpha/wiki/release.md"
printf '# 배포 순서\n\nCI 가 끝난 뒤에 설치한다.\n' > "$TMP/proj/beta/wiki/release.md"
printf '# 날씨\n\n오늘은 맑다.\n' > "$TMP/proj/gamma/wiki/weather.md"
find_in() { "$PY" "$RECALL" "$1" --root "$TMP/proj" --mode rag --min-coverage 0.4 --cwd "$2" --shared-topics "${3-}" 2>&1; }
out="$(find_in "배포 순서 CI 설치" /work/Alpha/app)"
case "$out" in *alpha/wiki*) case "$out" in *beta/wiki*) bad "다른 프로젝트 주제까지 붙였다: $out" ;; *) ok "작업 폴더의 프로젝트 주제만 붙인다 (대소문자·하위 폴더 무관)" ;; esac ;; *) bad "같은 프로젝트 주제를 못 붙였다: $out" ;; esac
out="$(find_in "배포 순서 CI 설치" /work/delta)"
[ -z "$out" ] && ok "어느 주제의 프로젝트도 아니면 붙이지 않는다" || bad "다른 프로젝트 주제를 붙였다: $out"
out="$(find_in "beta 배포 순서 CI 설치" /work/delta)"
case "$out" in *beta/wiki*) ok "메시지가 주제 이름을 말하면 그 주제는 붙인다" ;; *) bad "이름을 말했는데 못 붙였다: $out" ;; esac
out="$(find_in "배포 순서 CI 설치" /work/delta "gamma, beta")"
case "$out" in *beta/wiki*) ok "공용 주제(--shared-topics)는 늘 붙인다" ;; *) bad "공용 주제를 못 붙였다: $out" ;; esac
# --- 핵심 낱말이 하나뿐이면 기본 기준(낱말 2개)에는 안 걸리고, 낮춘 기준(--min-shared 1)에는 걸린다
out="$("$PY" "$RECALL" "배포" --root "$TMP/proj" --mode rag --min-coverage 0.4 --cwd /work/alpha 2>&1)"
[ -z "$out" ] && ok "낱말 하나는 기본 기준에 걸리지 않는다" || bad "낱말 하나가 기본 기준에 걸렸다: $out"
out="$("$PY" "$RECALL" "배포" --root "$TMP/proj" --mode rag --min-coverage 0.2 --min-shared 1 --cwd /work/alpha 2>&1)"
case "$out" in *alpha/wiki/release.md*) ok "낮춘 기준(0.2·1)이면 낱말 하나로도 찾는다" ;; *) bad "낮춘 기준인데 못 찾았다: $out" ;; esac
# --- 깊게 찾기의 발췌 모드(스킬 설명의 명령): 문구마다 그 낱말이 모두 든 덩어리를 모두 찍는다.
#     덩어리 12개 중 10개에 든 '공통'은 9% 를 넘어 흔한 문구로 빠진다
mkdir -p "$TMP/excerpt/farm/wiki"
{
  printf '# 농장 기록\n\n딸기 수확 시기는 봄이다.\n\n수박 수확은 여름이다.\n'
  for note_number in 1 2 3 4 5 6 7 8 9 10; do printf '\n공통 메모 %s 번째.\n' "$note_number"; done
} > "$TMP/excerpt/farm/wiki/notes.md"
excerpt() { printf "$1" | "$PY" "$RECALL" --excerpt --root "$TMP/excerpt" --cwd "$2" 2>&1; }
out="$(excerpt '딸기\n딸기 수확\n수박\n공통\n포도\n' /work/farm)"
case "$out" in *"[딸기, 딸기 수확] 딸기 수확 시기는 봄이다."*) ok "발췌: 여러 문구에 걸린 덩어리는 한 번만, 걸린 문구를 함께 적는다" ;; *) bad "발췌가 겹치거나 문구가 빠졌다: $out" ;; esac
case "$out" in *"[수박] 수박 수확은 여름이다."*) ok "발췌: 문구마다 따로 찾아 다른 주제의 덩어리도 모은다" ;; *) bad "두 번째 주제를 못 모았다: $out" ;; esac
case "$out" in *"흔해서 뺀 문구: 공통(덩어리 10개)"*) case "$out" in *"공통 메모"*) bad "흔한 문구의 덩어리를 찍었다: $out" ;; *) ok "발췌: 흔한 문구는 알리고 뺀다" ;; esac ;; *) bad "흔한 문구를 알리지 않았다: $out" ;; esac
case "$out" in *"찾지 못한 문구: 포도"*) ok "발췌: 못 찾은 문구를 알린다" ;; *) bad "못 찾은 문구를 알리지 않았다: $out" ;; esac
case "$out" in *"== $TMP/excerpt/farm/wiki/notes.md"*) ok "발췌: 출처 페이지를 적는다" ;; *) bad "출처가 없다: $out" ;; esac
out="$(excerpt '딸기\n' /work/other)"; code=$?
[ -z "$out" ] && [ "$code" -ne 0 ] && ok "발췌: 다른 프로젝트 주제는 찾지 않는다" || bad "발췌가 다른 프로젝트 주제를 찾았다: $out"
out="$(prompt_hook '{"prompt":"플러그인을 업데이트했는데 훅이 그대로야, 왜 그래?","cwd":"/work/other-project"}')"
[ -z "$out" ] && ok "훅은 작업 폴더를 넘겨 다른 프로젝트 위키를 붙이지 않는다" || bad "훅이 다른 프로젝트 위키를 붙였다: $out"
printf 'not json' | sh "$REPO/hooks/run.sh" wiki-recall >/dev/null 2>&1 \
  && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all wiki-recall checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
