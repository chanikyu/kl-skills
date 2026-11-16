#!/bin/sh
# Checks bash-offload: a long Bash output goes to a file and only its head, tail and path stay
# in the conversation; a short one is untouched; the exit code survives; commands the wrapper
# could break (exit, exec, set -e, background jobs) are left alone; KL_OFFLOAD=0 turns it off.
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
  echo "skip  no python3 — bash-offload selftest skipped"
  exit 0
fi

export KL_OFFLOAD_DIR="$TMP/outputs"
# 훅에 Bash 이벤트를 주고, 바뀐 명령(없으면 원래 명령)을 돌려준다
rewritten() {  # $1 명령, $2 추가 입력 칸(JSON 객체, 없으면 {})
  extra="${2:-}"; [ -n "$extra" ] || extra='{}'
  "$PY" -c 'import json,sys; print(json.dumps({"session_id":"s1","tool_name":"Bash","tool_input":dict({"command":sys.argv[1]}, **json.loads(sys.argv[2]))}))' "$1" "$extra" \
    | sh "$REPO/hooks/run.sh" bash-offload 2>/dev/null \
    | "$PY" -c 'import json,sys
raw = sys.stdin.read()
print(json.loads(raw)["hookSpecificOutput"]["updatedInput"]["command"] if raw.strip() else sys.argv[1], end="")' "$1"
}

# --- 짧은 출력은 그대로, 종료 코드도 그대로
cmd="$(rewritten 'echo hello; false')"
out="$(cd "$TMP" && bash -c "$cmd" 2>&1)"; code=$?
[ "$out" = "hello" ] && ok "짧은 출력은 그대로 보인다" || bad "짧은 출력이 바뀌었다: $out"
[ "$code" -eq 1 ] && ok "종료 코드를 그대로 돌려준다" || bad "종료 코드 $code"

# --- 긴 출력은 앞뒤만 남기고 파일로 뺀다
cmd="$(rewritten 'seq 1 5000')"
out="$(cd "$TMP" && bash -c "$cmd" 2>&1)"; code=$?
lines="$(printf '%s\n' "$out" | wc -l | tr -d ' ')"
[ "$lines" -lt 200 ] && ok "긴 출력은 대화에 짧게 남는다 (${lines}줄)" || bad "긴 출력이 그대로 남았다 (${lines}줄)"
case "$out" in 1*"offload"*"5000"*) ok "앞부분·안내·끝부분이 남는다" ;; *) bad "앞뒤가 안 남았다: $(printf '%s' "$out" | head -3)" ;; esac
saved="$(printf '%s\n' "$out" | grep -o "$KL_OFFLOAD_DIR/[^ ]*\.log" | head -1)"
[ -n "$saved" ] && [ "$(wc -l < "$saved" | tr -d ' ')" -eq 5000 ] && ok "전체 출력은 파일에 다 있다" || bad "저장 파일이 없거나 모자란다: $saved"
[ "$code" -eq 0 ] && ok "긴 출력에서도 종료 코드를 지킨다" || bad "종료 코드 $code"

# --- 디렉터리 이동은 그대로 이어진다 (같은 셸에서 돈다)
cmd="$(rewritten "cd $TMP && pwd")"
out="$(bash -c "$cmd" 2>&1)"
case "$out" in *"$TMP"*) ok "cd 와 같은 셸 상태를 깨지 않는다" ;; *) bad "cd 가 깨졌다: $out" ;; esac

# --- 감싸면 깨질 수 있는 명령은 건드리지 않는다
for risky in 'exit 3' 'exec ls' 'set -e; false' 'sleep 1 &' 'set -o errexit; ls'; do
  [ "$(rewritten "$risky")" = "$risky" ] && ok "그대로 둔다: $risky" || bad "감쌌다: $risky"
done
[ "$(rewritten 'seq 1 5000' '{"run_in_background": true}')" = "seq 1 5000" ] && ok "백그라운드 실행은 그대로 둔다" || bad "백그라운드 실행을 감쌌다"
[ "$(KL_OFFLOAD=0 rewritten 'seq 1 5000')" = "seq 1 5000" ] && ok "KL_OFFLOAD=0 이면 꺼진다" || bad "꺼지지 않는다"

# --- 다른 입력 칸(description, timeout)은 그대로 넘긴다
kept="$("$PY" -c 'import json; print(json.dumps({"session_id":"s1","tool_name":"Bash","tool_input":{"command":"ls","description":"list","timeout":5000}}))' \
  | sh "$REPO/hooks/run.sh" bash-offload 2>/dev/null)"
case "$kept" in *'"description": "list"'*'"timeout": 5000'*) ok "다른 입력 칸을 지킨다" ;; *) bad "입력 칸이 빠졌다: $kept" ;; esac
printf 'not json' | sh "$REPO/hooks/run.sh" bash-offload >/dev/null 2>&1 && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all bash-offload checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
