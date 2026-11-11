#!/bin/sh
# Checks that the README tells the truth about the repo: the counts in its tables,
# and that every skill, gate and selftest is listed. A README with counts in it
# goes stale the day a skill is added — this is the test that notices.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
README="$REPO/README.md"
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — readme selftest skipped"
  exit 0
fi

# 실제 개수: 스킬 폴더, hooks.json 의 게이트(배너 제외), 셀프테스트 파일
skill_count="$(ls -d "$REPO"/skills/*/ | wc -l | tr -d ' ')"
test_count="$(ls "$REPO"/tests/selftest*.sh | wc -l | tr -d ' ')"
gates="$("$PY" -c '
import json, sys
hooks = json.load(open(sys.argv[1]))["hooks"]
names = {hook["command"].split()[-1] for groups in hooks.values() for group in groups for hook in group["hooks"]}
print(" ".join(sorted(names)))' "$REPO/hooks/hooks.json")"
gate_count="$(printf '%s\n' $gates | grep -vc '^session-start$')"

# README 안에서 개수를 말하는 자리는 모두 실제와 같아야 한다
check_count() {  # $1 이름, $2 실제 개수, $3 README 에서 숫자를 뽑는 정규식(숫자는 그룹 1)
  wrong="$("$PY" - "$README" "$2" "$3" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
said = re.findall(sys.argv[3], text)
print(" ".join(n for n in said if n != sys.argv[2]) if said else "없음")
PYEOF
)"
  case "$wrong" in
    "")   ok "README 의 $1 개수가 실제($2)와 같다" ;;
    없음) bad "README 에서 $1 개수를 찾지 못했다" ;;
    *)    bad "README 의 $1 개수($wrong)가 실제($2)와 다르다" ;;
  esac
}
check_count "스킬" "$skill_count" '스킬\s*\|?\s*(\d+)개'
check_count "훅 게이트" "$gate_count" '훅 게이트\s*\|\s*(\d+)개'
check_count "셀프테스트" "$test_count" '셀프테스트\s*\|?\s*(\d+)묶음'

# 하나하나 빠짐없이 적혀 있는가
missing=""
for dir in "$REPO"/skills/*/; do
  name="$(basename "$dir")"
  grep -q "| \`$name\` |" "$README" || missing="$missing $name"
done
[ -z "$missing" ] && ok "스킬 ${skill_count}개가 모두 스킬 표에 있다" || bad "스킬 표에 없는 스킬:$missing"

missing=""
for gate in $gates; do
  grep -q "| \`$gate\` |" "$README" || missing="$missing $gate"
done
[ -z "$missing" ] && ok "hooks.json 의 게이트가 모두 게이트 표에 있다" || bad "게이트 표에 없는 게이트:$missing"

missing=""
for file in "$REPO"/tests/selftest*.sh; do
  name="$(basename "$file")"
  grep -q "$name" "$README" || missing="$missing $name"
done
[ -z "$missing" ] && ok "셀프테스트 ${test_count}개가 모두 README 에 있다" || bad "README 에 없는 셀프테스트:$missing"

echo
if [ "$fails" -eq 0 ]; then
  echo "all readme checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
