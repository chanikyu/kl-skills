#!/bin/sh
# Checks skill-match: a message that clearly belongs to a skill names it, everyday
# messages stay silent, and the trigger words come from the skills' own SKILL.md
# and the data files — not from the gate's code.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — skill-match selftest skipped"
  exit 0
fi

ask() { "$PY" -c 'import json,sys; print(json.dumps({"prompt": sys.argv[1]}, ensure_ascii=False))' "$1" \
        | sh "$REPO/hooks/run.sh" skill-match 2>/dev/null; }
expect() {  # $1 메시지, $2 기대하는 스킬
  case "$(ask "$1")" in
    *"kl-skills:$2"*) ok "\"$1\" → $2" ;;
    *)                bad "\"$1\" 에 $2 가 안 붙었다" ;;
  esac
}
silent() {  # $1 메시지
  out="$(ask "$1")"
  [ -z "$out" ] && ok "\"$1\" → 조용하다" || bad "\"$1\" 에 붙였다: $out"
}

# 사용자가 2026-11-13 에 짚은 네 스킬
expect "gut microbiome dysbiosis가 원인인지 결과인지 리서치 부탁해" research-to-wiki
expect "이 내용 위키에 정리해줘" llm-wiki-docs
expect "다음 분기 로드맵이랑 기획서 써줘" planner
expect "파이프라인 돌렸는데 traceback 이 나와. 원인 찾아줘" pipeline-debug

# 위키·README 의 영어 예시 문장 (2026-11-13: 한 낱말 1점이라 안 붙던 것들)
expect "Research whether X causes Y" research-to-wiki
expect "Plan this with the planner" planner
expect "Write a roadmap for X" planner
expect "Find the root cause of this error" pipeline-debug
expect "Put this in the wiki" llm-wiki-docs

# 흔한 낱말만 있는 말, 짧은 말
silent "README 이름 좀 정리해줘"
silent "그래"
silent "오늘 저녁 메뉴는 무엇으로 할지 고민이다"

# 작업 끝 알림은 사람이 쓴 메시지가 아니다 (2026-11-13: 알림 속 "crash, error" 로 pipeline-debug 를 권했다)
silent "$(printf '<task-notification>\n<summary>Agent finished: no crash, no error, checklist ok</summary>\n</task-notification>')"

# 이미 훅이 매번 적용하는 스킬은 알리지 않는다
case "$(ask "작업 보고를 쉽게 설명해줘, 결과 정리도")" in
  *"natural-answering"*) bad "늘 적용되는 스킬까지 알렸다" ;;
  *)                     ok "훅이 늘 적용하는 스킬(natural-answering)은 알리지 않는다" ;;
esac

# 발동 말은 SKILL.md 와 데이터 파일에서 온다 — 게이트 코드에 박혀 있지 않다
grep -q "리서치\|traceback\|로드맵" "$REPO/hooks/py/skill-match.py" && bad "발동 말이 게이트 코드에 박혀 있다" \
  || ok "발동 말은 SKILL.md 와 데이터 파일에서 읽는다"

printf 'not json' | sh "$REPO/hooks/run.sh" skill-match >/dev/null 2>&1 && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all skill-match checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
