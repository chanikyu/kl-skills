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
# 직접 못 돌리니, 깨지는 꼴을 찾는다: 함수 머리·모듈·클래스 타입 표시의 list[...]·X | Y,
# from __future__ import annotations(3.7), :=(3.8), 위치 전용 인자 /(3.8), 그리고 3.7 이후에 생긴 함수·인자
# 이름(2026-11-19: check_drift.py 의 date.fromisoformat 은 3.7 부터라 3.6 에서 plan-drift 가 조용히 죽었다).
# 게이트가 부르는 skills/*/scripts 도 같은 python3 로 돌므로 함께 본다.
REPO="$(dirname "$(dirname "$RUN")")"
python_cmd=""
for candidate in python3 python; do command -v "$candidate" >/dev/null 2>&1 && { python_cmd="$candidate"; break; }; done

# 3.6 은 로케일이 UTF-8 이 아니면(LANG 이 비었거나 C) 표준 입출력을 ascii 로 쓴다. 그러면 한글을 내보내는
# 게이트가 UnicodeEncodeError 로 죽는다(2026-11-19 재현). 3.7 부터는 파이썬이 스스로 UTF-8 로 바꾸므로,
# 그 전환을 끈 C 로케일로 3.6 을 흉내 낸다. 흉내가 안 되는 python3 면(그래도 한글이 써지면) 건너뛴다.
if [ -n "$python_cmd" ]; then
  korean_payload='{"session_id":"locale-test","hook_event_name":"UserPromptSubmit","prompt":"체크리스트 만들어 줘","transcript_path":"/nonexistent","cwd":"/tmp"}'
  c_locale() { env -u PYTHONIOENCODING HOME="$TMP/home" KL_CHECKLIST_DIR="$TMP/checklists" \
                   LC_ALL=C LANG=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0 "$@"; }
  if printf '%s' "$korean_payload" | c_locale "$python_cmd" "$REPO/hooks/py/checklist-start.py" checklist-start >/dev/null 2>&1; then
    echo "skip  this python writes Korean even in the C locale, so the 3.6 locale case cannot be imitated"
  else
    out="$(printf '%s' "$korean_payload" | c_locale CLAUDE_PLUGIN_ROOT="$REPO" sh "$RUN" checklist-start 2>&1)"
    rc=$?
    case "$out" in
      *항목*) [ $rc -eq 0 ] && ok "a Korean-writing gate survives a non-UTF-8 locale (python 3.6 server)" \
                || bad "C locale: rc=$rc" ;;
      *) bad "C locale: gate died or wrote nothing (rc=$rc): $(printf '%s' "$out" | tail -1)" ;;
    esac
  fi
fi

# 입력이 UTF-8 이 아니어도 게이트는 죽지 않는다: 모두 _hook_output.read_payload 로 읽는다.
# 2026-11-13 리뷰가 sys.stdin.read() 가 깨진 바이트에서 죽는 것을 재현했고, 2026-11-19 남은 7개도 옮겼다.
# 3.15 는 UTF-8 모드가 기본이라 깨진 바이트를 대체 글자로 넘기므로, 3.6~3.14 에 UTF-8 로케일일 때처럼 엄격하게
# 읽도록(utf-8:strict) 강제한다. KL_GATES_DIR 은 이 검사를 다른 게이트 폴더(고치기 전 사본)에 돌려 볼 때만 쓴다.
if [ -n "$python_cmd" ]; then
  died_on_bytes=""
  for gate in "${KL_GATES_DIR:-$REPO/hooks/py}"/[a-z]*.py; do
    printf '\377\376{"prompt":"\351"}' | env PYTHONIOENCODING=utf-8:strict HOME="$TMP/home" KL_CHECKLIST_DIR="$TMP/checklists" \
        LLM_WIKI_ROOT="$TMP/no-wiki" "$python_cmd" "$gate" "$(basename "$gate" .py)" >/dev/null 2>&1 \
      || died_on_bytes="$died_on_bytes $(basename "$gate")"
  done
  [ -z "$died_on_bytes" ] && ok "every python gate survives input that is not UTF-8" \
    || bad "died on input that is not UTF-8:$died_on_bytes"
fi

if [ -n "$python_cmd" ]; then
  cat > "$TMP/old_python_check.py" <<'EOF'
import ast
import pathlib
import sys

BUILTIN_GENERICS = {"list", "dict", "tuple", "set", "frozenset", "type"}
# 3.6 에 없는 함수·인자 이름과 생긴 판. 다른 뜻으로 같은 이름을 쓰는 코드도 잡히지만, 그때는 이름을 바꾸는 편이 싸다.
NEWER_NAMES = {"fromisoformat": "3.7", "isascii": "3.7", "reconfigure": "3.7", "capture_output": "3.7",
               "missing_ok": "3.8", "dirs_exist_ok": "3.8",
               "removeprefix": "3.9", "removesuffix": "3.9", "is_relative_to": "3.9"}
# 이 검사는 CI 에서 진짜 3.6 으로도 돈다(.github/workflows/tests.yml). 3.8 에 생긴 노드를 바로 부르면
# 검사기가 먼저 죽으므로 없으면 건너뛴다 — 3.6 에서는 그 문법이 ast.parse 의 구문 오류로 먼저 걸린다.
NAMED_EXPR = getattr(ast, "NamedExpr", None)


def too_new(annotation):
    """3.6 이 타입 표시를 계산할 때 깨지는 꼴인가: list[...] 같은 내장 제네릭, X | Y."""
    for node in ast.walk(annotation):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in BUILTIN_GENERICS:
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return True
    return False


hits = []
paths = sorted(path for folder in sys.argv[1:] for path in pathlib.Path(folder).glob("*.py"))
for path in paths:
    shown = "/".join(path.parts[-3:])
    tree = ast.parse(path.read_text(encoding="utf-8"))
    evaluated = [s for s in tree.body if isinstance(s, ast.AnnAssign)]   # 모듈 수준 표시는 읽을 때 계산된다
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            evaluated += [s for s in node.body if isinstance(s, ast.AnnAssign)]
        if isinstance(node, ast.ImportFrom) and node.module == "__future__" \
                and any(alias.name == "annotations" for alias in node.names):
            hits.append("%s:%d from __future__ import annotations" % (shown, node.lineno))
        if NAMED_EXPR is not None and isinstance(node, NAMED_EXPR):
            hits.append("%s:%d :=" % (shown, node.lineno))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            posonly = getattr(node.args, "posonlyargs", [])
            params = posonly + node.args.args + node.args.kwonlyargs
            if posonly:
                hits.append("%s:%d %s: positional-only /" % (shown, node.lineno, node.name))
            marks = [p.annotation for p in params if p.annotation] + ([node.returns] if node.returns else [])
            if any(too_new(mark) for mark in marks):
                hits.append("%s:%d %s: annotation" % (shown, node.lineno, node.name))
        newer = node.attr if isinstance(node, ast.Attribute) else node.arg if isinstance(node, ast.keyword) else None
        if newer in NEWER_NAMES:
            hits.append("%s:%d %s (python %s)" % (shown, getattr(node, "lineno", 0), newer, NEWER_NAMES[newer]))
    hits += ["%s:%d variable annotation" % (shown, s.lineno) for s in evaluated if too_new(s.annotation)]
print("\n".join(hits))
EOF
  old_python_hits="$("$python_cmd" "$TMP/old_python_check.py" "$(dirname "$RUN")/py" "$REPO"/skills/*/scripts 2>&1)"
  [ -z "$old_python_hits" ] && ok "python gates and the skill scripts they run use nothing newer than python 3.6" \
    || bad "python gates break on an old python3 (3.6): $old_python_hits"
fi

[ "$fails" -eq 0 ] || { echo "$fails check(s) failed"; exit 1; }
echo "all checks passed"
