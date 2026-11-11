#!/bin/sh
# Checks the gate that reads a python file right after it is written.
#
# The silent cases carry the weight here. This gate fires on every Write and Edit,
# so one wrong complaint — about a cached file, a markdown note, a clean module —
# is enough for someone to switch the whole thing off.
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
  echo "skip  no python3 — code-check selftest skipped"
  exit 0
fi

export CLAUDE_PLUGIN_ROOT="$REPO"
gate() { printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$1" \
         | sh "$REPO/hooks/run.sh" code-check 2>/dev/null; }

printf 'def f(p):\n    s = p\n    return s\n' > "$TMP/bad.py"
cat > "$TMP/good.py" <<'EOF'
"""이름과 설명을 스킬대로 쓴 예제."""


def shout(message_text):
    """받은 말을 대문자로 돌려준다. 비교할 때 대소문자를 무시하기 때문이다."""
    return message_text.upper()
EOF
printf '# 노트\n\n`a = 1` 같은 글.\n' > "$TMP/notes.md"
mkdir -p "$TMP/.venv/lib/site-packages"
cp "$TMP/bad.py" "$TMP/.venv/lib/site-packages/vendored.py"

out="$(gate "$TMP/bad.py")"
case "$out" in
  *vague-name*) ok "나쁜 이름을 그 자리에서 알려 준다" ;;
  *)            bad "아무 말도 하지 않았다: $out" ;;
esac
case "$out" in
  *"막지는 않는다"*) ok "막지 않는다고 분명히 밝힌다" ;;
  *)                 bad "막지 않는다는 말이 없다" ;;
esac
printf '%s' "$out" | "$PY" -c "import json,sys; d=json.load(sys.stdin); assert d['hookSpecificOutput']['hookEventName']=='PostToolUse'; assert d['hookSpecificOutput']['additionalContext'].strip()" 2>/dev/null \
  && ok "출력이 모델에게 닿는 모양(additionalContext JSON)이다" \
  || bad "출력이 JSON 이 아니다 — 기록에만 남고 모델은 못 받는다: $out"

out="$(gate "$TMP/good.py")"
[ -z "$out" ] && ok "스킬대로 쓴 파일에는 조용하다" || bad "잘 쓴 파일에 말했다: $out"

out="$(gate "$TMP/notes.md")"
[ -z "$out" ] && ok "파이썬이 아닌 파일은 건너뛴다" || bad "마크다운을 검사했다: $out"

out="$(gate "$TMP/.venv/lib/site-packages/vendored.py")"
[ -z "$out" ] && ok "남이 만든 패키지는 건너뛴다" || bad "site-packages 를 지적했다: $out"

out="$(gate "$TMP/does-not-exist.py")"
[ -z "$out" ] && ok "없는 파일에는 조용하다" || bad "없는 파일에 말했다: $out"

printf 'not json' | sh "$REPO/hooks/run.sh" code-check >/dev/null 2>&1 \
  && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"
printf '' | sh "$REPO/hooks/run.sh" code-check >/dev/null 2>&1 \
  && ok "빈 입력에도 0으로 끝난다" || bad "빈 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all code-check checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
