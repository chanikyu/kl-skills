#!/bin/sh
# Checks the code checker: each rule must fire on the case it is for, and a file
# written the way the skill asks must stay silent. The silent half matters most —
# a checker that complains about good code gets switched off within a day.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CHECK="$REPO/skills/readable-code/scripts/check_code.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — readable-code selftest skipped"
  exit 0
fi

# --- 규칙마다 한 경우씩. 파일 맨 위 설명문도 일부러 비워 둔다.
cat > "$TMP/bad.py" <<'EOF'
import os


def f(p):
    s = os.path.basename(p)
    tmp = s.upper()
    data = tmp + "!"
    return data


def long_one(paths):
    collected = []
    for one_path in paths:
        name = os.path.basename(one_path)
        if not name:
            continue
        if name.startswith("."):
            continue
        if name.endswith(".md"):
            collected.append(name)
        elif name.endswith(".py"):
            collected.append(name.upper())
        else:
            collected.append(name.lower())
    collected.sort()
    while len(collected) > 100:
        collected.pop()
    if not collected:
        return ""
    if len(collected) == 1:
        return collected[0]
    joined = ",".join(collected)
    return joined
EOF

# --- 같은 일을 스킬이 말하는 대로 쓴 파일
cat > "$TMP/good.py" <<'EOF'
"""파일 이름만 모아서 돌려주는 작은 예제."""
import os


def basename_upper(file_path):
    """경로에서 파일 이름만 떼어 대문자로 만든다.

    대문자로 만드는 것은 뒤에서 대소문자를 구분하지 않고 비교하기 때문이다.
    """
    file_name = os.path.basename(file_path)
    return file_name.upper()
EOF

out="$("$PY" "$CHECK" --all "$TMP/bad.py" 2>&1)"
for code in vague-name no-docstring uncommented-long-function no-module-docstring; do
  case "$out" in
    *"[$code]"*) ok "걸림: $code" ;;
    *)           bad "안 걸림: $code" ;;
  esac
done
for name in "'f'" "'p'" "'s'" "'tmp'" "'data'"; do
  case "$out" in
    *"$name"*) ok "이름 지적: $name" ;;
    *)         bad "이름을 놓쳤다: $name" ;;
  esac
done
# 반복 번호와 버리는 값은 예외다. 이걸 지적하면 모든 for 문이 걸린다.
case "$out" in
  *"'one_path'"*) bad "충분히 설명적인 이름을 지적했다" ;;
  *)              ok "설명적인 이름은 넘어간다" ;;
esac

# --- 잘 쓴 파일은 조용해야 한다
good="$("$PY" "$CHECK" --all "$TMP/good.py" 2>&1)"
case "$good" in
  *"경고 0건, 참고 0건"*) ok "스킬대로 쓴 파일은 아무 지적이 없다" ;;
  *)                      bad "잘 쓴 파일에 지적이 났다: $good" ;;
esac

# --- 판정 기준은 데이터 파일에서 온다
cp -R "$REPO/skills/readable-code/data" "$TMP/data"
printf 'p\n' >> "$TMP/data/short-names-ok.txt"
out2="$("$PY" "$CHECK" --data-dir "$TMP/data" "$TMP/bad.py" 2>&1)"
case "$out2" in
  *"이름 'p' 로는"*) bad "허용 목록에 넣은 이름을 아직도 지적한다" ;;
  *)                 ok "허용 목록에 넣으면 지적하지 않는다" ;;
esac

# --- 종료 코드: 찾으면 1, --exit-zero 면 0 (훅은 작업을 막으면 안 된다)
"$PY" "$CHECK" "$TMP/bad.py" >/dev/null 2>&1 && bad "지적이 있는데 0으로 끝났다" \
  || ok "지적이 있으면 1로 끝난다"
"$PY" "$CHECK" --exit-zero "$TMP/bad.py" >/dev/null 2>&1 && ok "--exit-zero 는 0으로 끝난다" \
  || bad "--exit-zero 인데 1로 끝났다"

# --- 파이썬이 아닌 파일은 손대지 않는다
printf 'a = 1 뭐든\n' > "$TMP/notes.txt"
out3="$("$PY" "$CHECK" "$TMP/notes.txt" 2>&1)"
case "$out3" in
  *"경고 0건"*) ok "파이썬이 아닌 파일은 건너뛴다" ;;
  *)            bad "파이썬 아닌 파일을 검사했다: $out3" ;;
esac

# --- 구문이 깨진 파일: 그 사실만 보고하고 터지지 않는다
printf 'def broken(:\n    pass\n' > "$TMP/broken.py"
out4="$("$PY" "$CHECK" "$TMP/broken.py" 2>&1)"
case "$out4" in
  *syntax-error*) ok "구문 오류를 그 사실로 보고한다" ;;
  *)              bad "구문 오류를 조용히 넘겼다: $out4" ;;
esac

echo
if [ "$fails" -eq 0 ]; then
  echo "all readable-code checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
