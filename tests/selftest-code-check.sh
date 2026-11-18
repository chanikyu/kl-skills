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

# --- git 저장소의 파일은 마지막 커밋에 없던 이름만 지적한다. 옛 이름까지 지적하면 "김에" 고치게 된다.
if command -v git >/dev/null 2>&1; then
  GREPO="$TMP/repo with space"
  mkdir -p "$GREPO/pkg"
  # 사용자의 전역 설정(서명, 커밋 훅)이 시험 저장소에 끼어들지 않게 막는다.
  gc() { dir="$1"; shift
         git -C "$dir" -c user.name=t -c user.email=t@example.com -c commit.gpgsign=false \
             -c core.hooksPath=/dev/null "$@" >/dev/null 2>&1; }
  OLD="$GREPO/pkg/old.py"
  write_old() {  # 이미 있던 파일. 나쁜 이름과 설명문 없는 함수가 일부러 남아 있다.
    cat > "$OLD" <<EOF
"""이미 있던 파일."""


def f(p):
    s = p
    return s


def long_one(count):
    total = count
    total += 1
    total += 2
    total += ${1:-3}
    return total
EOF
  }
  write_old
  gc "$GREPO" init -q
  gc "$GREPO" add -A
  gc "$GREPO" commit -q -m init

  out="$(gate "$OLD")"
  [ -z "$out" ] && ok "커밋 그대로인 파일에는 조용하다" || bad "바뀐 것 없는 파일에 말했다: $out"

  write_old 4   # 기존 함수 본문의 숫자 한 줄만 바꾼다
  out="$(gate "$OLD")"
  [ -z "$out" ] && ok "한 줄만 고치면 손대지 않은 줄의 이름·설명문은 지적하지 않는다" \
                || bad "손대지 않은 줄을 지적했다: $out"

  write_old
  sed '/total += 2/d' "$OLD" > "$OLD.tmp" && mv "$OLD.tmp" "$OLD"   # 지우기만 한 변경
  out="$(gate "$OLD")"
  [ -z "$out" ] && ok "줄을 지우기만 한 변경에는 조용하다" || bad "지운 변경에 말했다: $out"

  write_old
  sed 's/    s = p$/    s = p.strip()/' "$OLD" > "$OLD.tmp" && mv "$OLD.tmp" "$OLD"
  out="$(gate "$OLD")"
  [ -z "$out" ] && ok "옛 이름이 든 줄을 고쳐도 그 옛 이름은 지적하지 않는다" \
                || bad "고친 줄의 옛 이름을 지적했다(함수 전체 이름을 바꾸라는 뜻이 된다): $out"

  write_old
  sed 's/def long_one(count):/def long_one(count, step=1):/' "$OLD" > "$OLD.tmp" && mv "$OLD.tmp" "$OLD"
  out="$(gate "$OLD")"
  [ -z "$out" ] && ok "기존 함수에 인자를 더해도 그 함수의 빠진 설명문은 지적하지 않는다" \
                || bad "기존 함수의 설명문을 요구했다: $out"

  write_old
  cat >> "$OLD" <<'EOF'


def helper(rows):
    tmp = rows
    tmp = tmp + rows
    tmp = tmp + rows
    tmp = tmp + rows
    return tmp
EOF
  out="$(gate "$OLD")"
  case "$out" in
    *"'tmp'"*) ok "새로 쓴 줄의 나쁜 이름은 그대로 지적한다" ;;
    *)         bad "새로 쓴 나쁜 이름을 놓쳤다: $out" ;;
  esac
  case "$out" in
    *"'helper'"*) ok "새로 쓴 함수의 빠진 설명문은 그대로 지적한다" ;;
    *)            bad "새 함수의 설명문 빠짐을 놓쳤다: $out" ;;
  esac
  case "$out" in
    *"'f'"*|*"'p'"*|*"'s'"*|*"'long_one'"*) bad "새 줄과 함께 옛 줄까지 지적했다: $out" ;;
    *)                                       ok "새 줄을 더해도 옛 줄은 지적하지 않는다" ;;
  esac
  case "$out" in
    *"없던 이름만"*) ok "새 이름만 봤다고 밝힌다" ;;
    *)               bad "새 이름만 봤다는 말이 없다: $out" ;;
  esac

  cp "$TMP/bad.py" "$GREPO/pkg/new.py"   # 저장소 안이지만 아직 커밋한 적 없는 새 파일
  out="$(gate "$GREPO/pkg/new.py")"
  case "$out" in
    *vague-name*) ok "커밋한 적 없는 새 파일은 전부 본다" ;;
    *)            bad "새 파일을 건너뛰었다: $out" ;;
  esac

  FRESH="$TMP/fresh"   # 커밋이 하나도 없는 저장소 — 비교할 HEAD 가 없다
  mkdir -p "$FRESH"
  cp "$TMP/bad.py" "$FRESH/staged.py"
  gc "$FRESH" init -q
  gc "$FRESH" add staged.py
  out="$(gate "$FRESH/staged.py")"
  case "$out" in
    *vague-name*) ok "커밋이 없는 저장소의 파일은 전부 본다" ;;
    *)            bad "커밋 없는 저장소에서 아무 말도 안 했다: $out" ;;
  esac
else
  echo "skip  no git — 바뀐 줄만 보는 시험을 건너뛴다"
fi

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
