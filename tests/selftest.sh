#!/bin/sh
# Checks the one piece of logic that can silently pick the wrong file:
# run.sh mapping uname output -> binary name, and its never-break-a-session rule.
set -u

RUN="$(CDPATH= cd -- "$(dirname -- "$0")/../hooks" && pwd)/run.sh"
fails=0

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

[ "$fails" -eq 0 ] || { echo "$fails check(s) failed"; exit 1; }
echo "all checks passed"
