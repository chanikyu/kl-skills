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

# 대화를 실제 기록 모양 그대로 적는다. 각 항목은 [역할, 글, 기록 표시].
# 표시에 "str": true 가 있으면 내용을 블록 목록이 아니라 문자열로 쓴다(사람 메시지가 그렇다).
make_conversation() {
  "$PY" - "$1" "$2" <<'PYEOF'
import json, sys
out_path, spec = sys.argv[1], json.loads(sys.argv[2])
with open(out_path, "w", encoding="utf-8") as handle:
    for role, text, flags in spec:
        as_string = flags.pop("str", False)
        content = text if as_string else [{"type": "text", "text": text}]
        handle.write(json.dumps(dict(flags, message={"role": role, "content": content}),
                                ensure_ascii=False) + "\n")
PYEOF
}
HUMAN='{"str": true, "origin": {"kind": "human"}}'

# --- 2026-11-11 오탐: 사람이 한 번 요청했는데, 기록 속 기계 글(규칙 묶음·요약문·훅 피드백·
#     파일 읽기 결과)을 사람 메시지로 세서 '무엇' 을 다시 물었다고 막았다.
make_conversation "$TMP/machine.jsonl" "[
  [\"user\", \"gut microbiome dysbiosis가 질병을 초래하는지 리서치 부탁해\", $HUMAN],
  [\"assistant\", \"둘 다입니다.\", {}],
  [\"user\", \"<system-reminder>\\n무엇을 지켜야 하나? 규칙 묶음\\n</system-reminder>\", {}],
  [\"user\", \"This session is being continued. 무엇을 했나?\", {\"str\": true, \"isCompactSummary\": true}],
  [\"user\", \"Stop hook feedback: 무엇을 고칠까?\", {\"str\": true, \"isMeta\": true}],
  [\"user\", \"<system-reminder>\\nCalled the Read tool. 무엇?\\n</system-reminder>\", {}],
  [\"assistant\", \"둘 다입니다. 염증이 세균을 바꾸기도 합니다.\", {}]
]"
out="$(gate "$TMP/machine.jsonl")"
case "$out" in
  *"다시 물었다"*) bad "기계가 넣은 글을 사람의 되물음으로 셌다: $out" ;;
  *)              ok "요약문·규칙 묶음·훅 피드백은 사람 메시지로 세지 않는다" ;;
esac

# --- 한 번만 요청: 새 질문이 앞 질문과 의문사('왜')만 같다면 되물음이 아니다
make_conversation "$TMP/new-question.jsonl" "[
  [\"user\", \"왜 고쳐야 해?\", $HUMAN],
  [\"assistant\", \"이름이 모호해서입니다.\", {}],
  [\"user\", \"그럼 테스트는 왜 따로 둬?\", $HUMAN],
  [\"assistant\", \"훅마다 실패 모양이 달라서입니다.\", {}]
]"
out="$(gate "$TMP/new-question.jsonl")"
case "$out" in
  *"다시 물었다"*) bad "의문사만 같은 새 질문을 되물음으로 셌다: $out" ;;
  *)              ok "의문사만 겹치는 새 질문은 되물음이 아니다" ;;
esac

# --- 같은 짧은 말을 두 번 해도(승인·재시작 알림) 되물음이 아니다
make_conversation "$TMP/short-repeat.jsonl" "[
  [\"user\", \"다시 시작했어.\", $HUMAN],
  [\"assistant\", \"훅 9개가 실렸습니다.\", {}],
  [\"user\", \"다시 시작했어.\", $HUMAN],
  [\"assistant\", \"이번에도 9개가 실렸습니다.\", {}]
]"
out="$(gate "$TMP/short-repeat.jsonl")"
case "$out" in
  *"다시 물었다"*) bad "질문이 아닌 같은 알림을 되물음으로 셌다: $out" ;;
  *)              ok "질문이 아닌 같은 말 반복은 되물음이 아니다" ;;
esac

# --- 잘못 답해서 다시 요청: 되묻는 말투 (이 저장소에서 실제로 온 메시지)
make_conversation "$TMP/reask-marker.jsonl" "[
  [\"user\", \"뭐가 문제길래 고쳐야 해?\", $HUMAN],
  [\"assistant\", \"모호한 이름이 51건입니다.\", {}],
  [\"user\", \"뭔 소리인지 모르겠다니까???\", $HUMAN],
  [\"assistant\", \"길어서가 아니라 이름이 뜻을 안 알려줘서입니다.\", {}]
]"
out="$(gate "$TMP/reask-marker.jsonl")"
case "$out" in
  *"다시 물었다"*"2번째"*) ok "되묻는 말투('모르겠다니까')를 알아보고 몇 번째인지 말한다" ;;
  *)                      bad "되묻는 말투를 놓쳤다: $out" ;;
esac

# --- 잘못 답해서 다시 요청: 거의 같은 질문을 또 보냈다
make_conversation "$TMP/reask-same.jsonl" "[
  [\"user\", \"로그 파일은 어디에 저장돼?\", $HUMAN],
  [\"assistant\", \"로그는 중요합니다.\", {}],
  [\"user\", \"로그 파일은 어디에 저장되는데?\", $HUMAN],
  [\"assistant\", \"results 폴더입니다.\", {}]
]"
out="$(gate "$TMP/reask-same.jsonl")"
case "$out" in
  *"다시 물었다"*) ok "거의 같은 질문을 다시 보내면 되물음으로 본다" ;;
  *)              bad "같은 질문 재전송을 놓쳤다: $out" ;;
esac

# --- 여러 번 요청: 세 번째 되물음은 3번째라고 알린다
make_conversation "$TMP/reask-third.jsonl" "[
  [\"user\", \"왜 바꾸려는 거야?\", $HUMAN],
  [\"assistant\", \"83건입니다.\", {}],
  [\"user\", \"그러니까 왜 바꾸는지 이유를 알려줘야지???\", $HUMAN],
  [\"assistant\", \"함수가 깁니다.\", {}],
  [\"user\", \"아니.... 내 질문 이해가 안되니????\", $HUMAN],
  [\"assistant\", \"고칠 필요는 없습니다.\", {}]
]"
out="$(gate "$TMP/reask-third.jsonl")"
case "$out" in
  *"3번째"*) ok "여러 번 되물으면 몇 번째인지 센다" ;;
  *)         bad "되물음 횟수를 못 셌다: $out" ;;
esac

# --- 답을 받기 전에 같은 메시지가 또 들어왔다(재전송·대기열): 답이 틀려서 다시 물은 것이 아니다
make_conversation "$TMP/resent.jsonl" "[
  [\"user\", \"로그 파일은 어디에 저장돼?\", $HUMAN],
  [\"user\", \"로그 파일은 어디에 저장돼?\", $HUMAN],
  [\"assistant\", \"results 폴더입니다.\", {}]
]"
out="$(gate "$TMP/resent.jsonl")"
case "$out" in
  *"다시 물었다"*) bad "답 없이 재전송된 메시지를 되물음으로 셌다: $out" ;;
  *)              ok "답을 받기 전의 재전송은 되물음이 아니다" ;;
esac

# --- 지시 뒤에 "했니?" 로 확인하는 것은 되물음이 아니다 (2026-11-11 실제 메시지)
make_conversation "$TMP/confirm.jsonl" "[
  [\"user\", \"natural-answering은 항상 작동이 되어야지\", $HUMAN],
  [\"assistant\", \"Stop 훅에 걸었습니다.\", {}],
  [\"user\", \"natural-answering은 항상 작동이 되게 했니?\", $HUMAN],
  [\"assistant\", \"네, 매 턴 끝에 검사합니다.\", {}]
]"
out="$(gate "$TMP/confirm.jsonl")"
case "$out" in
  *"다시 물었다"*) bad "지시 뒤 확인 질문을 되물음으로 셌다: $out" ;;
  *)              ok "지시 뒤의 확인 질문은 되물음이 아니다" ;;
esac

# --- 사람이 코드나 태그를 붙여 넣으며 되물어도 사람 메시지다 ("<" 로 시작해도 origin 이 사람이면)
make_conversation "$TMP/paste.jsonl" "[
  [\"user\", \"이 태그가 왜 안 보여?\", $HUMAN],
  [\"assistant\", \"CSS 문제입니다.\", {}],
  [\"user\", \"<div> 이거 왜 안되는지 모르겠다니까\", $HUMAN],
  [\"assistant\", \"div 가 닫히지 않았습니다.\", {}]
]"
out="$(gate "$TMP/paste.jsonl")"
case "$out" in
  *"다시 물었다"*) ok "'<' 로 시작하는 사람 메시지도 사람 말로 센다" ;;
  *)              bad "'<' 로 시작한 사람의 되물음을 기계 글로 뺐다: $out" ;;
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
# 모양이 틀린 입력: JSON 이지만 객체가 아니거나, 경로가 비었거나, 기록 줄이 객체가 아니다
for payload in '[]' '"x"' '{"transcript_path":null}' '{"transcript_path":123}'; do
  printf '%s' "$payload" | "$PY" "$REPO/hooks/py/answer-check.py" >/dev/null 2>&1 \
    && ok "모양이 틀린 입력 $payload 에도 0으로 끝난다" || bad "모양이 틀린 입력 $payload 에 터졌다"
done
printf 'null\n[1]\n{"message":null}\n{"message":"x"}\n' > "$TMP/odd-lines.jsonl"
gate "$TMP/odd-lines.jsonl" >/dev/null && ok "객체가 아닌 기록 줄은 건너뛴다" || bad "객체가 아닌 기록 줄에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all answer-check checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
