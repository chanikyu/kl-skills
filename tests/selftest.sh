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

[ "$fails" -eq 0 ] || { echo "$fails check(s) failed"; exit 1; }
echo "all checks passed"
