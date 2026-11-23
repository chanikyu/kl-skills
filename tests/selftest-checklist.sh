#!/bin/sh
# Checks the two checklist gates: checklist-start keeps the last list, carries its open items
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
case "$out" in *"질문: A인가 B인가"*"→ 확인:"*) ok "뜻이 둘이면 먼저 묻기와 '→ 확인:' 을 매번 알린다" ;; *) bad "질문·확인 안내가 없다: $out" ;; esac
mkdir -p "$KL_CHECKLIST_DIR"; printf -- '# 지시: 끝난 일\n- [x] 다 한 일\n- [~] 못 한 일 — 사용자가 미뤘다\n' > "$LIST"
start "다음 지시" >/dev/null
[ ! -f "$LIST" ] && [ -f "$KL_CHECKLIST_DIR/s1.prev.md" ] && ok "다 끝난 목록은 새 지시가 오면 .prev 로 보관한다" \
  || bad "다 끝난 목록을 치우지 않았다"
out="$(start "")"
[ -z "$out" ] && ok "빈 메시지에는 조용하다" || bad "빈 메시지에 말했다"

# --- 안 끝난 항목은 새 지시가 와도 사라지지 않는다. 2026-11-18 사용자: "중간에 끊겨서 더 깊은 대화를 하면
# --- 체크리스트가 사라지는 거 같아. 그러면 안 되거든" — 곁 질문 하나에 하던 일의 목록이 .prev 로 치워졌다.
printf -- '# 지시: 릴리스\n- [x] 커밋\n- [ ] 푸시 → 확인: push 종료 0\n- [ ] 보고\n' > "$LIST"
out="$(start "\$8 이게 뭔데")"
[ -f "$KL_CHECKLIST_DIR/s1.prev.md" ] && grep -q '\[x\] 커밋' "$KL_CHECKLIST_DIR/s1.prev.md" \
  && ok "지난 목록 전체는 .prev 에 그대로 남긴다" || bad "지난 목록을 .prev 에 남기지 않았다"
[ -f "$LIST" ] && grep -q '^- \[ \] 푸시 → 확인: push 종료 0$' "$LIST" && grep -q '^- \[ \] 보고$' "$LIST" \
  && ok "안 끝난 항목은 새 목록으로 넘어온다" || bad "안 끝난 항목이 새 목록에 없다: $(cat "$LIST" 2>/dev/null)"
grep -q '커밋' "$LIST" && bad "끝난 항목까지 넘어왔다" || ok "끝난 항목은 넘어오지 않는다"
grep -q '릴리스' "$LIST" && ok "넘어온 항목에 원래 지시 제목이 붙는다" || bad "원래 지시 제목이 없다"
case "$out" in *"넘어온"*"2개"*"푸시"*) ok "메시지마다 넘어온 항목을 보여 준다" ;; *) bad "넘어온 항목을 알리지 않았다: $out" ;; esac
case "$out" in *"덮어쓰지"*) ok "덮어쓰지 말고 덧붙이라고 알린다" ;; *) bad "덮어쓰지 말라는 말이 없다: $out" ;; esac

# 답이 끝날 때: 넘어온 항목도 안 끝났으면 막는다
printf -- '\n## 지시: $8 이게 뭔데\n- [x] 질문에 답한다\n' >> "$LIST"
out="$(check)"
case "$out" in *'"decision": "block"'*"2개 남았다"*"푸시"*) ok "넘어온 항목이 남았으면 막는다" ;; *) bad "넘어온 항목을 놓쳤다: $out" ;; esac

# 넘어온 항목을 목록에서 지우면(덮어쓰기) 막는다 — 끝난 것처럼 보이지만 사라진 것이다
printf -- '# 지시: $8 이게 뭔데\n- [x] 질문에 답한다\n' > "$LIST"
out="$(check)"
case "$out" in *'"decision": "block"'*"사라졌다"*"푸시"*"보고"*) ok "넘어온 항목이 사라지면 막는다" ;; *) bad "사라진 항목을 놓쳤다: $out" ;; esac

# 넘어온 항목을 닫으면 통과한다. '→ 확인:' 뒤에 결과를 덧붙여도 같은 항목으로 본다
printf -- '## 넘어온 항목 — 지시: 릴리스\n- [x] 푸시 → 확인: push 종료 0, 3bcebc8\n- [~] 보고 — 사용자가 미뤘다\n\n# 지시: $8\n- [x] 질문에 답한다\n' > "$LIST"
out="$(check)"
[ -z "$out" ] && ok "넘어온 항목을 닫으면 통과한다(확인 결과를 덧붙여도)" || bad "닫은 넘어온 항목을 막았다: $out"

# 다 닫힌 뒤 새 지시가 오면 넘어올 것이 없다: 목록을 치우고 넘어온 기록도 지운다
start "그다음 지시" >/dev/null
[ ! -f "$LIST" ] && [ ! -f "$KL_CHECKLIST_DIR/s1.carry.md" ] && ok "다 닫힌 뒤에는 넘어온 기록도 지운다" \
  || bad "다 닫혔는데 목록이나 넘어온 기록이 남았다"
out="$(check)"
case "$out" in *"사라졌다"*) bad "지난번에 넘어온 항목을 이번에도 찾았다: $out" ;; *) ok "닫힌 넘어온 항목은 다음 지시를 막지 않는다" ;; esac
# 넘어온 항목을 지운 채 두 번째 Stop(막지 않음)까지 지나가도, 다음 지시에서 다시 넘어온다
printf -- '# 지시: 하던 일\n- [ ] 남은 일\n' > "$LIST"
start "곁 질문" >/dev/null
printf -- '# 지시: 곁 질문\n- [x] 답\n' > "$LIST"
check ',"stop_hook_active":true' >/dev/null
start "다음 지시" >/dev/null
grep -q '^- \[ \] 남은 일$' "$LIST" && ok "지워진 넘어온 항목은 다음 지시에서 다시 넘어온다" \
  || bad "지워진 넘어온 항목이 영영 사라졌다: $(cat "$LIST" 2>/dev/null)"
rm -f "$LIST" "$KL_CHECKLIST_DIR/s1.prev.md" "$KL_CHECKLIST_DIR/s1.carry.md"

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

# --- "→ 확인:" 을 붙인 항목도 같게 센다 (task-checklist 2단계의 형식)
printf -- '- [x] 게이트 추가 → 확인: 막는 시험 통과\n- [ ] 커밋하기 → 확인: git log 에 보인다\n' > "$LIST"
out="$(check)"
case "$out" in *'"decision": "block"'*"1개 남았다"*"커밋하기 → 확인: git log"*) ok "확인 방법이 붙은 안 끝난 항목을 그대로 짚는다" ;; *) bad "확인 방법이 붙은 항목을 잘못 셌다: $out" ;; esac
printf -- '- [x] 게이트 추가 → 확인: 막는 시험 통과\n- [~] 푸시 → 확인: 원격 — 사용자가 미뤘다\n' > "$LIST"
out="$(check)"
[ -z "$out" ] && ok "확인 방법이 붙은 항목도 끝났으면 통과한다" || bad "끝난 항목을 막았다: $out"

# --- 다 끝났으면 조용하다
printf -- '- [x] README 고치기\n- [X] 커밋하기\n' > "$LIST"
out="$(check)"
[ -z "$out" ] && ok "모두 끝났으면 조용히 통과한다" || bad "다 끝났는데 막았다: $out"

# --- 한 번 돌려보낸 뒤에는 막지 않는다 (무한 반복 방지)
printf -- '- [ ] 커밋하기\n' > "$LIST"
# 알림은 표준 오류로 간다. Stop 에서 0으로 끝나며 그냥 글을 찍으면 코덱스가 잘못된 출력으로 띄운다.
out="$(check ',"stop_hook_active":true')"
told="$(printf '{"session_id":"s1","stop_hook_active":true}' | sh "$REPO/hooks/run.sh" checklist-check 2>&1 >/dev/null)"
case "$out$told" in *'"decision"'*) bad "두 번째에도 막았다" ;; *"막지 않음"*) ok "두 번째에는 남은 항목을 알리기만 한다" ;; *) bad "예상 밖 출력: $out$told" ;; esac
[ -z "$out" ] && ok "두 번째 알림은 표준 출력에 찍지 않는다(코덱스 Stop 규칙)" || bad "Stop 표준 출력에 그냥 글을 찍었다: $out"

# --- 다른 세션의 목록은 보지 않는다
out="$(printf '{"session_id":"other"}' | sh "$REPO/hooks/run.sh" checklist-check 2>/dev/null)"
case "$out" in *"other.md"*) ok "세션마다 자기 목록만 본다" ;; *) bad "다른 세션 목록을 봤다: $out" ;; esac

# --- 2026-11-20 코덱스: 모델이 쓸 수 있는 자리는 작업 폴더·/tmp·$TMPDIR 뿐이라 ~/.claude 에 못 쓰고, 끝낼 때마다
#     막혔다. 코덱스(플러그인 훅에 PLUGIN_ROOT 를 넘긴다)에서는 $TMPDIR 아래에 둔다. Claude Code 는 그대로다.
CODEX_TMP="$TMP/codex-tmp"; mkdir -p "$CODEX_TMP" "$TMP/home"
codex_gate() { printf '%s' "$2" | env -u KL_CHECKLIST_DIR PLUGIN_ROOT="$REPO" TMPDIR="$CODEX_TMP" HOME="$TMP/home" \
                 sh "$REPO/hooks/run.sh" "$1" 2>/dev/null; }
out="$(codex_gate checklist-start '{"session_id":"cx1","prompt":"README 고쳐줘"}')"
case "$out" in *"$CODEX_TMP/kl-skills/checklists/cx1.md"*) ok "코덱스에서는 체크리스트를 \$TMPDIR 아래에 두라고 알린다" ;;
  *) bad "코덱스에서 쓸 수 없는 자리를 알렸다: $out" ;; esac
[ -d "$CODEX_TMP/kl-skills/checklists" ] && ok "코덱스용 체크리스트 폴더는 훅이 미리 만든다" || bad "코덱스용 체크리스트 폴더가 없다"
printf -- '- [ ] 커밋하기\n' > "$CODEX_TMP/kl-skills/checklists/cx1.md"
out="$(codex_gate checklist-check '{"session_id":"cx1"}')"
case "$out" in *'"decision": "block"'*"커밋하기"*) ok "코덱스에서도 같은 자리의 목록을 읽어 막는다" ;; *) bad "코덱스 자리의 목록을 못 읽었다: $out" ;; esac
out="$(printf '{"session_id":"cl1","prompt":"README 고쳐줘"}' | env -u KL_CHECKLIST_DIR -u PLUGIN_ROOT HOME="$TMP/home" \
       sh "$REPO/hooks/run.sh" checklist-start 2>/dev/null)"
case "$out" in *"$TMP/home/.claude/checklists/cl1.md"*) ok "Claude Code 에서는 그대로 ~/.claude/checklists 에 둔다" ;;
  *) bad "Claude Code 의 체크리스트 자리가 바뀌었다: $out" ;; esac

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
