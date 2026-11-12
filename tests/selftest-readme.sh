#!/bin/sh
# Checks that the READMEs tell the truth about the repo, in every language: the
# counts in their tables, every skill and gate listed, every image present, and
# the language links pointing at files that exist. The file map in
# docs/DEVELOPMENT.md must list every selftest. A README with counts in it goes
# stale the day a skill is added — this is the test that notices.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DEVELOPMENT="$REPO/docs/DEVELOPMENT.md"
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — readme selftest skipped"
  exit 0
fi

# 실제 개수: 스킬 폴더, hooks.json 의 게이트(배너 제외)
skill_count="$(ls -d "$REPO"/skills/*/ | wc -l | tr -d ' ')"
gates="$("$PY" -c '
import json, sys
hooks = json.load(open(sys.argv[1]))["hooks"]
names = {hook["command"].split()[-1] for groups in hooks.values() for group in groups for hook in group["hooks"]}
print(" ".join(sorted(names)))' "$REPO/hooks/hooks.json")"
gate_count="$(printf '%s\n' $gates | grep -vc '^session-start$')"

# README 안에서 개수를 말하는 자리는 모두 실제와 같아야 한다
check_count() {  # $1 파일, $2 이름, $3 실제 개수, $4 숫자를 뽑는 정규식(숫자는 그룹 1)
  wrong="$("$PY" - "$1" "$3" "$4" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
said = re.findall(sys.argv[3], text)
print(" ".join(n for n in said if n != sys.argv[2]) if said else "없음")
PYEOF
)"
  case "$wrong" in
    "")   ok "$(basename "$(dirname "$1")")/README: $2 개수가 실제($3)와 같다" ;;
    없음) bad "$1 에서 $2 개수를 찾지 못했다" ;;
    *)    bad "$1 의 $2 개수($wrong)가 실제($3)와 다르다" ;;
  esac
}

# 언어별 README 와, 그 언어의 개수 표 모양
check_readme() {  # $1 파일, $2 스킬 개수 정규식, $3 게이트 개수 정규식
  readme="$1"
  [ -f "$readme" ] || { bad "README 가 없다: $readme"; return; }
  check_count "$readme" "스킬" "$skill_count" "$2"
  check_count "$readme" "훅 게이트" "$gate_count" "$3"
  missing=""
  for dir in "$REPO"/skills/*/; do
    name="$(basename "$dir")"
    grep -q "| \`$name\` |" "$readme" || missing="$missing $name"
  done
  [ -z "$missing" ] && ok "$readme: 스킬 ${skill_count}개가 모두 스킬 표에 있다" || bad "$readme: 스킬 표에 없는 스킬:$missing"
  missing=""
  for gate in $gates; do
    grep -q "| \`$gate\` |" "$readme" || missing="$missing $gate"
  done
  [ -z "$missing" ] && ok "$readme: 게이트가 모두 게이트 표에 있다" || bad "$readme: 게이트 표에 없는 게이트:$missing"
  # 그림과 언어 링크는 그 README 가 있는 폴더 기준이다
  folder="$(dirname "$readme")"
  missing=""
  for target in $(grep -oE '(src|href)="[^"#:]+\.(png|svg|md)"|\]\([^)#:]+\.md\)' "$readme" \
                  | sed -E 's/^(src|href)="//; s/"$//; s/^\]\(//; s/\)$//'); do
    [ -f "$folder/$target" ] || missing="$missing $target"
  done
  [ -z "$missing" ] && ok "$readme: 가리키는 그림·문서가 모두 있다" || bad "$readme: 없는 파일:$missing"
}

# 언어별 README 와 그 언어의 개수 표 모양. 언어를 더하면 여기 한 줄과, 각 README 의 언어 선택 줄을 더한다.
check_readme "$REPO/README.md"           '\|\s*Skills\s*\|\s*(\d+)\s*\|' '\|\s*Hook gates\s*\|\s*(\d+)\s*\|'
check_readme "$REPO/docs/ko-KR/README.md" '\|\s*스킬\s*\|\s*(\d+)개'       '\|\s*훅 게이트\s*\|\s*(\d+)개'
check_readme "$REPO/docs/ja-JP/README.md" '\|\s*スキル\s*\|\s*(\d+)\s*\|'   '\|\s*フックゲート\s*\|\s*(\d+)\s*\|'
check_readme "$REPO/docs/zh-CN/README.md" '\|\s*技能\s*\|\s*(\d+)\s*\|'     '\|\s*钩子检查\s*\|\s*(\d+)\s*\|'
check_readme "$REPO/docs/es/README.md"    '\|\s*Skills\s*\|\s*(\d+)\s*\|'   '\|\s*Hook gates\s*\|\s*(\d+)\s*\|'

# 언어 선택 줄: 모든 판이 나머지 판을 전부 가리킨다 (가리키는 파일이 있는지는 위에서 봤다)
language_count=5
for readme in "$REPO/README.md" "$REPO"/docs/*/README.md; do
  others="$(grep -oE '\]\([^)]*README\.md\)' "$readme" | sort -u | wc -l | tr -d ' ')"
  [ "$others" -eq $((language_count - 1)) ] && ok "${readme#$REPO/}: 언어 선택 줄이 나머지 $((language_count - 1))개 판을 가리킨다" \
    || bad "${readme#$REPO/}: 언어 선택 줄이 $others 개 판만 가리킨다"
done

# 개발 문서의 파일 지도는 셀프테스트를 하나도 빠뜨리지 않는다
missing=""
for file in "$REPO"/tests/selftest*.sh; do
  name="$(basename "$file")"
  grep -q "$name" "$DEVELOPMENT" || missing="$missing $name"
done
test_count="$(ls "$REPO"/tests/selftest*.sh | wc -l | tr -d ' ')"
[ -z "$missing" ] && ok "셀프테스트 ${test_count}개가 모두 개발 문서에 있다" || bad "개발 문서에 없는 셀프테스트:$missing"

echo
if [ "$fails" -eq 0 ]; then
  echo "all readme checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
