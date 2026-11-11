#!/bin/sh
# Picks how to run a gate on this machine and runs it.
#
#   run.sh <gate-name> [extra args...]
#
# Dispatch, in order:
#   1. hooks/py/<gate-name>.py exists  -> run it with python3 (or python)
#   2. otherwise                       -> bin/kl-gate-<this target> <gate-name>
#
# Python wins when its file is present because that is the prototyping path: write
# a gate in Python, and when it turns out to sit on a hot path (PreToolUse fires on
# every tool call) port it into kl-gate and delete the .py. hooks.json never changes,
# so the move costs one file deletion. The Rust binary handles every gate through one
# `match`, so the filesystem cannot tell which gates it implements — that is why the
# .py has to take precedence rather than the other way round.
#
# A hook must never break a session. If python is absent, no binary matches this
# OS/CPU, or the binary is missing, this exits 0 silently and the session continues
# ungated. A missing rule is a smaller problem than a session that will not start.
#
# KL_OS / KL_ARCH / KL_PY override uname and the interpreter list — test hooks only.
set -u

ROOT="${CLAUDE_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
GATE="${1:-}"

target() {
  os="${KL_OS:-$(uname -s)}"
  arch="${KL_ARCH:-$(uname -m)}"
  case "$os" in
    Darwin)
      case "$arch" in
        arm64|aarch64) echo "aarch64-apple-darwin" ;;
        x86_64)        echo "x86_64-apple-darwin" ;;
      esac ;;
    Linux)
      case "$arch" in
        aarch64|arm64) echo "aarch64-unknown-linux-musl" ;;
        x86_64)        echo "x86_64-unknown-linux-musl" ;;
      esac ;;
  esac
}

if [ "$GATE" = "--print-target" ]; then
  target
  exit 0
fi

# 1. Python gate
if [ -n "$GATE" ] && [ -f "$ROOT/hooks/py/$GATE.py" ]; then
  # Unquoted on purpose: KL_PY is a space-separated candidate list, and the test
  # suite sets it to a name that does not exist to cover the no-python path.
  # shellcheck disable=SC2086
  for py in ${KL_PY-python3 python}; do
    if command -v "$py" >/dev/null 2>&1; then
      exec "$py" "$ROOT/hooks/py/$GATE.py" "$@"
    fi
  done
  exit 0
fi

# 2. Rust gate
T="$(target)"
if [ -z "$T" ]; then
  exit 0
fi

BIN="$ROOT/bin/kl-gate-$T"
if [ ! -x "$BIN" ]; then
  exit 0
fi

exec "$BIN" "$@"
