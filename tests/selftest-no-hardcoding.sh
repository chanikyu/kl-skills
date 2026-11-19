#!/bin/sh
# Checks the no-hardcoding checker: machine-only absolute paths and long tables of values
# written into Python code, reported by the code-check gate.
#
# The silent cases weigh as much as the loud ones. A gate that fires on every Write and
# nags about a command line or a list of the code's own column names gets switched off.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CHECK="$REPO/skills/no-hardcoding/scripts/check_hardcoding.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — no-hardcoding selftest skipped"
  exit 0
fi

# 2026-11-19 재현: 절대경로·8항목 사전·임계값을 박은 파일에 어떤 검사도 아무 말을 하지 않았다.
cat > "$TMP/loud.py" <<'EOF'
"""값을 코드에 박은 예. 설명문 속 /Users/doc/example 은 실행되는 값이 아니다."""
import subprocess

# 주석 속 /Users/comment/x 도 잡지 않는다
SPECIES = {"asp": 1, "cys": 2, "fum": 3, "glu": 4, "his": 5, "ile": 6, "leu": 7, "lys": 8}
KNOWN = frozenset({"alpha", "beta", "gamma", "delta", "epsilon", "zeta"})
GRID = [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]]
OFFSETS: list = [-1, -2, -3, -4, -5, -6]
WINDOWS = "C:\\Users\\me\\data.csv"
COMMAND = "cat /home/me/notes.txt"


def load_counts():
    """임계값 0.05 는 잡지 않는다 — 코드에 둬도 되는 숫자와 기계로 가를 수 없다."""
    with open("/Users/someone/data/counts.tsv") as handle:
        return [line for line in handle if float(line.split()[1]) > 0.05]
EOF
out="$("$PY" "$CHECK" "$TMP/loud.py")"
rc=$?
for want in "loud.py:5 [long-literal] 'SPECIES'" "loud.py:6 [long-literal] 'KNOWN'" \
            "loud.py:7 [long-literal] 'GRID'" "loud.py:8 [long-literal] 'OFFSETS'" \
            "loud.py:9 [absolute-path]" "loud.py:10 [absolute-path]" "loud.py:15 [absolute-path]"; do
  case "$out" in
    *"$want"*) ;;
    *) bad "missed: $want" ;;
  esac
done
case "$out" in
  *"경고 7건"*) [ $rc -eq 1 ] && ok "paths and value tables in code are caught (7), docstring/comment/threshold are not" \
                || bad "found but exit code $rc, want 1" ;;
  *) bad "want exactly 7 warnings: $(printf '%s' "$out" | tail -1)" ;;
esac

cat > "$TMP/quiet.py" <<'EOF'
"""잡으면 안 되는 것들."""
import subprocess

FIVE = ["one", "two", "three", "four", "five"]
WITH_NAME = ["one", "two", "three", "four", "five", FIVE]
__all__ = ["aa", "bb", "cc", "dd", "ee", "ff", "gg"]
COLUMNS = ["turn", "fired", "exit_code", "seconds", "message", "output"]
URL = "https://example.com/home/user/x"
SCRATCH = "/tmp/work"


def run(row):
    """명령 줄 목록은 표가 아니다. 열 이름은 코드가 스스로 쓰는 낱말이다."""
    subprocess.run(["git", "log", "--oneline", "-n", "5", "--format=%h"], check=True)
    row["turn"], row["fired"], row["exit_code"] = 1, True, 0
    row["seconds"], row["message"] = 0.1, ""
    return "x".endswith((".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp"))
EOF
out="$("$PY" "$CHECK" "$TMP/quiet.py")"
rc=$?
{ [ $rc -eq 0 ] && case "$out" in *"경고 0건"*) true ;; *) false ;; esac; } \
  && ok "five items, mixed values, __all__, own column names, URLs, /tmp, call arguments stay silent" \
  || bad "quiet file was not quiet (rc=$rc): $out"

# --changed: 옛 표에 항목 하나를 더했다고 표 전체를 지적하면 손대지 않은 것을 "김에" 고치게 된다.
if command -v git >/dev/null 2>&1; then
  mkdir "$TMP/repo"
  printf '"""모듈."""\nOLD = ["k1", "k2", "k3", "k4", "k5", "k6"]\n' > "$TMP/repo/table.py"
  git -C "$TMP/repo" init -q && git -C "$TMP/repo" add table.py \
    && git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -qm init
  printf '"""모듈."""\nOLD = ["k1", "k2", "k3", "k4", "k5", "k6", "k7"]\nNEW = ["n1", "n2", "n3", "n4", "n5", "n6"]\n' \
    > "$TMP/repo/table.py"
  out="$("$PY" "$CHECK" --changed "$TMP/repo/table.py")"
  case "$out" in
    *"'NEW'"*"경고 1건"*) case "$out" in *"'OLD'"*) bad "--changed reported the old table: $out" ;;
                                        *) ok "--changed reports the new table only, not one that grew" ;; esac ;;
    *) bad "--changed: want only NEW: $out" ;;
  esac
else
  echo "skip  no git — --changed case skipped"
fi

# 훅: 코드 검사 게이트가 이 검사기도 부른다. 고친 예까지 모델에게 간다.
export CLAUDE_PLUGIN_ROOT="$REPO"
out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$TMP/loud.py" \
       | sh "$REPO/hooks/run.sh" code-check 2>/dev/null)"
case "$out" in
  *absolute-path*long-literal*|*long-literal*absolute-path*)
    case "$out" in
      *"no-hardcoding: 값을 코드 밖으로"*) ok "code-check gate passes the findings to the model" ;;
      *) bad "gate output has no no-hardcoding note: $out" ;;
    esac ;;
  *) bad "gate said nothing about hardcoded values: $out" ;;
esac
out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$TMP/quiet.py" \
       | sh "$REPO/hooks/run.sh" code-check 2>/dev/null)"
case "$out" in
  *no-hardcoding*) bad "gate complained about the quiet file: $out" ;;
  *) ok "code-check gate stays silent on the quiet file" ;;
esac

[ "$fails" -eq 0 ] || { echo "$fails check(s) failed"; exit 1; }
echo "all checks passed"
