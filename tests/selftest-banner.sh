#!/bin/sh
# The session-start banner says how many gates are live. That number lives in Rust
# source while the gates themselves live in hooks.json and hooks/py, so it goes stale
# the moment a gate is added — it did, twice, and a person had to notice both times.
# This compares the two.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
MAIN="$REPO/crates/kl-gate/src/main.rs"
HOOKS="$REPO/hooks/hooks.json"
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — banner selftest skipped"
  exit 0
fi

# 게이트 목록은 hooks.json 이 정본이다. 배너를 알리는 session-start 자신은 세지 않는다.
gates="$("$PY" - "$HOOKS" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
names = []
for entries in d["hooks"].values():
    for e in entries:
        for h in e["hooks"]:
            if h.get("id") == "session-start:banner":
                continue
            names.append(h["command"].rsplit(" ", 1)[-1].strip('"'))
print(" ".join(names))
EOF
)"
count=$(printf '%s' "$gates" | wc -w | tr -d ' ')
[ "$count" -gt 0 ] && ok "hooks.json 에 게이트 ${count}개" || bad "hooks.json 에서 게이트를 못 찾았다"

banner="$(tr -d '\n' < "$MAIN" | grep -o 'KL-SKILLS GATES[^;]*' || true)"
said=$(printf '%s' "$banner" | grep -o 'loaded, [0-9]*' | grep -o '[0-9]*' || echo "")
[ -n "$said" ] || bad "배너에서 개수를 못 읽었다"

if [ "$said" = "$count" ]; then
  ok "배너가 말하는 개수($said)와 hooks.json($count)이 같다"
else
  bad "배너는 $said개라고 하는데 hooks.json 에는 $count개다 — 게이트를 추가하고 배너를 안 고쳤다"
fi

for g in $gates; do
  case "$banner" in
    *"$g"*) ok "배너가 $g 를 적고 있다" ;;
    *)      bad "배너에 $g 가 없다" ;;
  esac
done

echo
if [ "$fails" -eq 0 ]; then
  echo "all banner checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
