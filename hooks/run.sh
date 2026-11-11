#!/bin/sh
# Picks the prebuilt kl-gate binary for this machine and runs it.
#
# A hook must never break a session. If no binary matches this OS/CPU, or the
# binary is missing, this exits 0 silently and the session continues ungated.
#
# KL_OS / KL_ARCH override uname — used only by tests/selftest.sh.
set -u

ROOT="${CLAUDE_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"

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

if [ "${1:-}" = "--print-target" ]; then
  target
  exit 0
fi

T="$(target)"
if [ -z "$T" ]; then
  exit 0
fi

BIN="$ROOT/bin/kl-gate-$T"
if [ ! -x "$BIN" ]; then
  exit 0
fi

exec "$BIN" "$@"
