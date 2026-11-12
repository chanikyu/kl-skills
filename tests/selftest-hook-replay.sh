#!/bin/sh
# Checks hook-replay: it must cut the transcript at the right moment for each event,
# call the gate the way Claude Code does, and leave a row per moment in the TSV.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
REPLAY="$REPO/.claude/skills/hook-replay/scripts/replay.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — hook-replay selftest skipped"
  exit 0
fi

# 사람 메시지 셋: 새 질문 → 되물음 → 새 요청. 사이에 기계 글이 끼어 있다.
"$PY" - "$TMP/talk.jsonl" <<'PYEOF'
import json, sys
human = {"origin": {"kind": "human"}}
rows = [
    ("user", "뭐가 문제길래 고쳐야 해?", human),
    ("assistant", "모호한 이름이 51건입니다.", {}),
    ("user", "<system-reminder>무엇을 지켜야 하나?</system-reminder>", {}),
    ("user", "뭔 소리인지 모르겠다니까???", human),
    ("assistant", "이름이 뜻을 안 알려줘서입니다.", {}),
    ("user", "알겠어. 그래프 열어줘", human),
    ("assistant", "열었습니다.", {}),
]
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    for role, text, flags in rows:
        content = text if role == "user" and flags else [{"type": "text", "text": text}]
        handle.write(json.dumps(dict(flags, message={"role": role, "content": content}),
                                ensure_ascii=False) + "\n")
PYEOF

# --- Stop 시점: 되물은 2번째에서만 answer-check 가 말해야 한다
"$PY" "$REPLAY" answer-check --transcript "$TMP/talk.jsonl" --out "$TMP/stop.tsv" >"$TMP/stop.log" 2>&1
[ -f "$TMP/stop.tsv" ] && ok "결과를 TSV 로 남긴다" || bad "결과 파일이 없다: $(cat "$TMP/stop.log")"
rows="$(tail -n +2 "$TMP/stop.tsv" | wc -l | tr -d ' ')"
[ "$rows" = "3" ] && ok "사람 메시지 3개 = 시점 3개 (기계 글은 시점이 아니다)" || bad "시점 수가 $rows 다"
fired="$(awk -F'\t' 'NR>1 && $2=="yes" {print $1}' "$TMP/stop.tsv" | tr '\n' ' ')"
[ "$fired" = "2 " ] && ok "되물은 2번째 시점에서만 훅이 말한다" || bad "말한 시점이 '$fired' 다"
case "$(cat "$TMP/stop.log")" in
  *"시점 3개 중 3개"*"말한 시점 1개"*) ok "요약 줄에 시점 수와 말한 횟수가 나온다" ;;
  *) bad "요약 줄이 이상하다: $(cat "$TMP/stop.log")" ;;
esac

# --- --last: 마지막 N개 시점만
"$PY" "$REPLAY" answer-check --transcript "$TMP/talk.jsonl" --out "$TMP/last.tsv" --last 1 >/dev/null 2>&1
first_turn="$(awk -F'\t' 'NR==2 {print $1}' "$TMP/last.tsv")"
[ "$first_turn" = "3" ] && ok "--last 1 은 마지막 시점만 돌린다" || bad "--last 1 이 $first_turn 번째부터 돌렸다"

# --- prompt 시점: 메시지는 기록이 아니라 prompt 로 간다. 받은 입력을 그대로 적는 가짜 게이트로 본다
FAKE="$TMP/fake-plugin"; mkdir -p "$FAKE/hooks/py"
cp "$REPO/hooks/py/_transcript.py" "$FAKE/hooks/py/"
cat > "$FAKE/hooks/run.sh" <<'EOF'
#!/bin/sh
# 받은 입력에서 prompt 와 기록 줄 수만 돌려준다
python3 -c 'import json,sys; e=json.load(sys.stdin); n=sum(1 for _ in open(e["transcript_path"])); print("%s|%d" % (e.get("prompt",""), n))'
EOF
"$PY" "$REPLAY" echo --transcript "$TMP/talk.jsonl" --out "$TMP/prompt.tsv" --event prompt \
      --plugin-root "$FAKE" >/dev/null 2>&1
second="$(awk -F'\t' 'NR==3 {print $6}' "$TMP/prompt.tsv")"
case "$second" in
  "뭔 소리인지 모르겠다니까???|3") ok "prompt 시점은 그 메시지 직전까지 자르고 메시지를 prompt 로 넘긴다" ;;
  *) bad "prompt 시점 입력이 틀렸다: '$second'" ;;
esac

# --- 없는 기록은 2로 끝나고 말해 준다
"$PY" "$REPLAY" answer-check --transcript "$TMP/none.jsonl" --out "$TMP/x.tsv" >/dev/null 2>&1
[ $? -eq 2 ] && ok "없는 기록 파일이면 2로 끝난다" || bad "없는 기록 파일 처리"

echo
if [ "$fails" -eq 0 ]; then
  echo "all hook-replay checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
