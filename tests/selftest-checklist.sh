#!/bin/sh
# Checks the two checklist gates: checklist-start moves the last turn's list aside
# and says where to write the new one; checklist-check blocks the answer once when
# the list is missing or has open items, and never blocks twice.
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
  echo "skip  no python3 — checklist selftest skipped"
  exit 0
fi

export KL_CHECKLIST_DIR="$TMP/checklists"
LIST="$KL_CHECKLIST_DIR/s1.md"
start() { printf '{"session_id":"s1","prompt":"%s"}' "$1" | sh "$REPO/hooks/run.sh" checklist-start 2>/dev/null; }
check() { printf '{"session_id":"s1"%s}' "${1:-}" | sh "$REPO/hooks/run.sh" checklist-check 2>/dev/null; }

# --- 메시지를 받으면: 어디에 쓸지 알리고, 지난 턴의 목록은 치운다
out="$(start "README 고치고 커밋해줘")"
case "$out" in *"$LIST"*) ok "체크리스트를 쓸 경로를 알린다" ;; *) bad "경로를 알리지 않았다: $out" ;; esac
mkdir -p "$KL_CHECKLIST_DIR"; printf -- '- [ ] 지난 턴에 남은 일\n' > "$LIST"
start "다음 지시" >/dev/null
[ ! -f "$LIST" ] && [ -f "$KL_CHECKLIST_DIR/s1.prev.md" ] && ok "새 지시가 오면 지난 목록은 .prev 로 보관한다" \
  || bad "지난 목록을 치우지 않았다"
out="$(start "")"
[ -z "$out" ] && ok "빈 메시지에는 조용하다" || bad "빈 메시지에 말했다"

# --- 기계가 보낸 알림은 지시가 아니다: 하던 목록을 치우지 않는다
# (2026-11-13: 백그라운드 작업 알림이 UserPromptSubmit 로 들어와 작업 중인 목록을 .prev 로 치웠다)
printf -- '- [ ] 하던 일\n' > "$LIST"; rm -f "$KL_CHECKLIST_DIR/s1.prev.md"
out="$("$PY" -c 'import json,sys; print(json.dumps({"session_id":"s1","prompt":sys.argv[1]}))' \
  "$(printf '<task-notification>\n<task-id>b1</task-id>\n<status>completed</status>\n</task-notification>')" \
  | sh "$REPO/hooks/run.sh" checklist-start 2>/dev/null)"
[ -f "$LIST" ] && [ ! -f "$KL_CHECKLIST_DIR/s1.prev.md" ] && [ -z "$out" ] && ok "작업 알림은 지시가 아니라 목록을 그대로 둔다" \
  || bad "작업 알림에 목록을 치웠다: $out"
printf -- '- [ ] 하던 일\n' > "$LIST"
out="$("$PY" -c 'import json,sys; print(json.dumps({"session_id":"s1","prompt":sys.argv[1]}))' \
  "$(printf '<agent-message from="a1">\n[Subagent hand-back] report\n</agent-message>')" \
  | sh "$REPO/hooks/run.sh" checklist-start 2>/dev/null)"
[ -f "$LIST" ] && [ -z "$out" ] && ok "서브에이전트 보고로 시작하는 알림도 목록을 그대로 둔다" || bad "서브에이전트 보고에 목록을 치웠다: $out"
rm -f "$LIST"

# --- 답이 끝날 때: 목록이 없으면 한 번 막는다
out="$(check)"
case "$out" in *'"decision": "block"'*"체크리스트가 없다"*) ok "체크리스트가 없으면 막는다" ;; *) bad "목록 없이 넘겼다: $out" ;; esac

# --- 안 끝난 항목이 있으면 그 항목을 짚어 막는다
printf -- '# 지시\n- [x] README 고치기\n- [ ] 커밋하기\n- [~] 푸시 — 사용자가 미뤘다\n' > "$LIST"
out="$(check)"
case "$out" in *'"decision": "block"'*"1개 남았다"*"커밋하기"*) ok "안 끝난 항목을 짚어 막는다" ;; *) bad "안 끝난 항목을 놓쳤다: $out" ;; esac
case "$out" in *"푸시"*) bad "[~] 로 닫은 항목까지 남았다고 했다" ;; *) ok "[~] 로 닫은 항목은 남은 것으로 세지 않는다" ;; esac

# --- 내용 없는 빈 칸도 안 끝난 항목이다 (2026-11-13 리뷰: 빈 '- [ ]' 가 조용히 통과했다)
printf -- '- [x] README 고치기\n- [ ]\n' > "$LIST"
out="$(check)"
case "$out" in *'"decision": "block"'*"1개 남았다"*) ok "내용 없는 '- [ ]' 도 남은 항목으로 센다" ;; *) bad "빈 칸을 놓쳤다: $out" ;; esac
printf -- '- [ ]\n- [x] 커밋하기\n' > "$LIST"
out="$(check)"
case "$out" in *"- [ ] - [x]"*) bad "빈 칸이 다음 줄과 붙어 보였다: $out" ;; *'"decision": "block"'*) ok "빈 칸이 다음 줄 항목과 붙지 않는다" ;; *) bad "예상 밖 출력: $out" ;; esac

# --- 다 끝났으면 조용하다
printf -- '- [x] README 고치기\n- [X] 커밋하기\n' > "$LIST"
out="$(check)"
[ -z "$out" ] && ok "모두 끝났으면 조용히 통과한다" || bad "다 끝났는데 막았다: $out"

# --- 한 번 돌려보낸 뒤에는 막지 않는다 (무한 반복 방지)
printf -- '- [ ] 커밋하기\n' > "$LIST"
out="$(check ',"stop_hook_active":true')"
case "$out" in *'"decision"'*) bad "두 번째에도 막았다" ;; *"막지 않음"*) ok "두 번째에는 남은 항목을 알리기만 한다" ;; *) bad "예상 밖 출력: $out" ;; esac

# --- 다른 세션의 목록은 보지 않는다
out="$(printf '{"session_id":"other"}' | sh "$REPO/hooks/run.sh" checklist-check 2>/dev/null)"
case "$out" in *"other.md"*) ok "세션마다 자기 목록만 본다" ;; *) bad "다른 세션 목록을 봤다: $out" ;; esac

# --- 입력이 깨져도 세션을 깨지 않는다
for gate in checklist-start checklist-check; do
  printf 'not json' | sh "$REPO/hooks/run.sh" "$gate" >/dev/null 2>&1 && ok "$gate: 깨진 입력에도 0으로 끝난다" || bad "$gate: 깨진 입력에 터졌다"
done

for gate in checklist-start checklist-check skill-match; do
  printf '\377\376' | sh "$REPO/hooks/run.sh" "$gate" >/dev/null 2>&1 && ok "$gate: UTF-8 이 아닌 입력에도 0으로 끝난다" || bad "$gate: UTF-8 이 아닌 입력에 터졌다"
done
echo
if [ "$fails" -eq 0 ]; then
  echo "all checklist checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
