#!/bin/sh
# Checks the one piece of logic that can silently pick the wrong file:
# run.sh mapping uname output -> binary name, and its never-break-a-session rule.
set -u

RUN="$(CDPATH= cd -- "$(dirname -- "$0")/../hooks" && pwd)/run.sh"
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

expect() { # os arch want
  got="$(KL_OS="$1" KL_ARCH="$2" sh "$RUN" --print-target)"
  if [ "$got" = "$3" ]; then
    echo "ok    $1/$2 -> ${3:-<none>}"
  else
    echo "FAIL  $1/$2 -> got '${got}', want '${3}'"
    fails=$((fails + 1))
  fi
}

expect Darwin  arm64   aarch64-apple-darwin
expect Darwin  aarch64 aarch64-apple-darwin
expect Darwin  x86_64  x86_64-apple-darwin
expect Linux   aarch64 aarch64-unknown-linux-musl
expect Linux   arm64   aarch64-unknown-linux-musl
expect Linux   x86_64  x86_64-unknown-linux-musl
expect FreeBSD x86_64  ""
expect Linux   riscv64 ""

# Unsupported platform, or bin/ not populated yet, must still exit 0:
# a hook that fails here would break every session on that machine.
KL_OS=FreeBSD KL_ARCH=x86_64 sh "$RUN" session-start </dev/null
if [ $? -eq 0 ]; then
  echo "ok    unsupported platform exits 0"
else
  echo "FAIL  unsupported platform did not exit 0"
  fails=$((fails + 1))
fi

CLAUDE_PLUGIN_ROOT=/nonexistent sh "$RUN" session-start </dev/null
if [ $? -eq 0 ]; then
  echo "ok    missing binary exits 0"
else
  echo "FAIL  missing binary did not exit 0"
  fails=$((fails + 1))
fi

# --- dispatch: a Python gate must win over the Rust binary, and must receive the
# --- gate name as argv[1] so Python and Rust gates share one contract.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/hooks/py" "$TMP/bin"
cp "$RUN" "$TMP/hooks/run.sh"
printf '%s\n' '#!/bin/sh' 'echo "RUST-RAN:$1"' > "$TMP/bin/kl-gate-$(sh "$RUN" --print-target)"
chmod +x "$TMP/bin/kl-gate-$(sh "$RUN" --print-target)"
printf '%s\n' 'import sys' 'print("PY-RAN:" + (sys.argv[1] if len(sys.argv) > 1 else ""))' \
  > "$TMP/hooks/py/demo.py"

out="$(CLAUDE_PLUGIN_ROOT="$TMP" sh "$TMP/hooks/run.sh" demo </dev/null 2>&1)"
[ "$out" = "PY-RAN:demo" ] && ok "python gate runs and gets the gate name" \
  || bad "python gate: got '$out', want 'PY-RAN:demo'"

out="$(CLAUDE_PLUGIN_ROOT="$TMP" sh "$TMP/hooks/run.sh" other </dev/null 2>&1)"
[ "$out" = "RUST-RAN:other" ] && ok "no .py for the gate falls back to the binary" \
  || bad "fallback: got '$out', want 'RUST-RAN:other'"

# No usable interpreter must skip the gate, not error out — this is the Windows
# case, where python is often absent. KL_PY stands in for "nothing found".
out="$(KL_PY=kl-no-such-python CLAUDE_PLUGIN_ROOT="$TMP" sh "$TMP/hooks/run.sh" demo </dev/null 2>&1)"
rc=$?
{ [ $rc -eq 0 ] && [ -z "$out" ]; } && ok "python absent exits 0 silently" \
  || bad "python absent: rc=$rc out='$out'"

# run.sh 는 그 기계의 python3 를 그대로 쓴다. 2026-11-18 기본 python3 가 3.6 인 서버에서 wiki-sync.py 가
# 읽히지 않았다: 함수 머리의 list[Path] 는 3.9 꼴이라 3.8 이하는 함수를 만들 때 멈춘다. 3.6 은 이 맥에 없어
# 직접 못 돌리니, 파일을 읽는 순간 깨지는 꼴만 찾는다: 함수 머리·모듈·클래스 타입 표시의 list[...]·X | Y,
# from __future__ import annotations(3.7), :=(3.8), 위치 전용 인자 /(3.8).
python_cmd=""
for candidate in python3 python; do command -v "$candidate" >/dev/null 2>&1 && { python_cmd="$candidate"; break; }; done
if [ -n "$python_cmd" ]; then
  cat > "$TMP/old_python_check.py" <<'EOF'
import ast
import pathlib
import sys

BUILTIN_GENERICS = {"list", "dict", "tuple", "set", "frozenset", "type"}


def too_new(annotation):
    """3.6 이 타입 표시를 계산할 때 깨지는 꼴인가: list[...] 같은 내장 제네릭, X | Y."""
    for node in ast.walk(annotation):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in BUILTIN_GENERICS:
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return True
    return False


hits = []
for path in sorted(pathlib.Path(sys.argv[1]).glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    evaluated = [s for s in tree.body if isinstance(s, ast.AnnAssign)]   # 모듈 수준 표시는 읽을 때 계산된다
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            evaluated += [s for s in node.body if isinstance(s, ast.AnnAssign)]
        if isinstance(node, ast.ImportFrom) and node.module == "__future__" \
                and any(alias.name == "annotations" for alias in node.names):
            hits.append("%s:%d from __future__ import annotations" % (path.name, node.lineno))
        if isinstance(node, ast.NamedExpr):
            hits.append("%s:%d :=" % (path.name, node.lineno))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            if node.args.posonlyargs:
                hits.append("%s:%d %s: positional-only /" % (path.name, node.lineno, node.name))
            marks = [p.annotation for p in params if p.annotation] + ([node.returns] if node.returns else [])
            if any(too_new(mark) for mark in marks):
                hits.append("%s:%d %s: annotation" % (path.name, node.lineno, node.name))
    hits += ["%s:%d variable annotation" % (path.name, s.lineno) for s in evaluated if too_new(s.annotation)]
print("\n".join(hits))
EOF
  old_python_hits="$("$python_cmd" "$TMP/old_python_check.py" "$(dirname "$RUN")/py" 2>&1)"
  [ -z "$old_python_hits" ] && ok "python gates have no load-time syntax newer than python 3.6" \
    || bad "python gates break on an old python3 (3.6): $old_python_hits"
fi

[ "$fails" -eq 0 ] || { echo "$fails check(s) failed"; exit 1; }
echo "all checks passed"
