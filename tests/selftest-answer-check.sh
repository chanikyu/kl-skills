#!/bin/sh
# Checks the gate that reads the answer a turn just produced.
#
# This is the only gate that can block a turn, so the test spends its weight on
# two things: that it blocks when the person had to ask twice, and that it cannot
# block forever. A gate that loops is worse than no gate.
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
  echo "skip  no python3 — answer-check selftest skipped"
  exit 0
fi

export CLAUDE_PLUGIN_ROOT="$REPO"

# 기록 파일을 만든다. 실제 대화 기록과 같은 모양(한 줄에 한 사건)이다.
make_transcript() {
  "$PY" - "$1" "$2" "$3" "$4" <<'PYEOF'
import json, sys
out_path, first_question, second_question, answer = sys.argv[1:5]
def turn(role, text):
    return json.dumps({"message": {"role": role,
                                   "content": [{"type": "text", "text": text}]}},
                      ensure_ascii=False)
with open(out_path, "w", encoding="utf-8") as handle:
    handle.write(turn("user", first_question) + "\n")
    handle.write(turn("assistant", "83건입니다. 모호한 이름 51건, 설명문 없음 22건.") + "\n")
    if second_question:
        handle.write(turn("user", second_question) + "\n")
    handle.write(turn("assistant", answer) + "\n")
PYEOF
}

gate() { printf '{"transcript_path":"%s"%s}' "$1" "${2:-}" \
         | sh "$REPO/hooks/run.sh" answer-check 2>/dev/null; }

# --- 같은 질문이 다시 왔다: 막아야 한다
make_transcript "$TMP/again.jsonl" "왜 고쳐야 해?" "그러니까 왜 고치는데???" "고칠 필요 없습니다."
out="$(gate "$TMP/again.jsonl")"
case "$out" in
  *'"decision": "block"'*) ok "되물었을 때 막는다" ;;
  *)                       bad "되물었는데 그냥 넘겼다: $out" ;;
esac
case "$out" in
  *repeated*|*"다시 물었다"*) ok "왜 막는지 이유를 말한다" ;;
  *)                          bad "이유가 없다: $out" ;;
esac

# --- 한 번 막은 뒤에는 다시 막지 않는다. 이게 없으면 턴이 끝나지 않는다
out="$(gate "$TMP/again.jsonl" ',"stop_hook_active":true')"
case "$out" in
  *'"decision"'*) bad "두 번째에도 막았다 — 무한 반복이 된다" ;;
  *"막지 않음"*)  ok "한 번 막은 뒤에는 알리고 넘긴다" ;;
  *)              bad "예상 밖 출력: $out" ;;
esac

# --- 되묻지 않고 짧게 답했으면 조용해야 한다
make_transcript "$TMP/clean.jsonl" "그래프 열어줘" "" "열었습니다. 6페이지 13링크입니다."
out="$(gate "$TMP/clean.jsonl")"
[ -z "$out" ] && ok "질문에 답한 짧은 글에는 조용하다" || bad "깨끗한 답에 말했다: $out"

# --- 화면 하나를 넘는 답
long_answer="$("$PY" -c "print('\n'.join('%d번째 줄입니다. 짧게 씁니다.' % n for n in range(1, 41)))")"
make_transcript "$TMP/long.jsonl" "상태 알려줘" "" "$long_answer"
out="$(gate "$TMP/long.jsonl")"
case "$out" in
  *"줄이다"*) ok "너무 긴 답변을 막는다" ;;
  *)          bad "긴 답변을 놓쳤다: $out" ;;
esac

# --- 기록이 없거나 입력이 깨져도 세션을 깨지 않는다
out="$(gate "$TMP/does-not-exist.jsonl")"
[ -z "$out" ] && ok "기록이 없으면 조용하다" || bad "없는 기록에 말했다: $out"
printf 'not json' | sh "$REPO/hooks/run.sh" answer-check >/dev/null 2>&1 \
  && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all answer-check checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
