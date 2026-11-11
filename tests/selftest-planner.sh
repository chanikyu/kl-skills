#!/bin/sh
# Checks check_plan.py: a plan that follows the frame must pass clean, and a plan
# whose goals do not cascade must be caught by name. The cascade is the rule the
# user stated most firmly — long-term first, mid-term serving it, short-term
# serving mid-term — so most fixtures here break it in a different way.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CHECK="$REPO/skills/planner/scripts/check_plan.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — planner selftest skipped"
  exit 0
fi

# --- 틀을 지키고 목표가 위아래로 이어지는 기획서
cat > "$TMP/good.md" <<'EOF'
# 사내 위키 검색 개선

## 0. 틀

- 분야: 서비스·웹
- 기간 규모: 프로젝트 규모 — 장기 6개월, 중기 분기, 단기 2주

## 1. 방향성 정의 및 핵심 도출

### 1-1. 문제점·기회 발견

직원 설문(2026-10, 응답 212명)에서 61%가 "찾는 문서가 안 나온다"고 답했다.

### 1-2. 목표·타깃 설정

타깃: 입사 1년 이내 직원

- [L1] 원하는 문서를 첫 검색에서 찾는 비율을 6개월 안에 80%로 — 기준: 검색 로그
- [M1.1] 1분기 안에 제목·본문 동의어 사전을 만든다 — 기준: 동의어 300쌍
- [S1.1.1] 2주 안에 검색 실패 로그 상위 100건을 분류한다 — 기준: 100건

### 1-3. 타당성·경쟁력 검토

기존 검색 엔진의 동의어 기능을 쓰므로 새 개발은 없다. 외부 도구 대비 비용이 0원이다.

### 1-4. 기능 정의·컨셉

컨셉: 직원이 쓰는 말로 찾아도 나온다.

- 동의어 사전 관리 화면 — 위한 목표: M1.1
- 검색 실패 로그 보기 — 위한 목표: S1.1.1

## 2. 문서화 및 설계

### 2-1. 요구사항 정의서·기능명세서

동의어를 추가하면 다음 검색부터 반영된다. 확인: 추가 직후 검색해서 결과가 바뀌는지 본다.

### 2-2. 정보 구조·플로우차트

관리자 메뉴 아래 "동의어" 항목. 검색 → 결과 없음 → 실패 로그 기록 순서로 흐른다.

### 2-3. 와이어프레임·화면 설계서

동의어 목록 화면 하나와 추가 대화상자 하나.

### 2-4. 일정·유관부서 조율

S1.1.1 은 1~2주차 기획자. 개발 부서(architect)는 검색 엔진 설정만으로 된다고 답했다.
EOF

out="$("$PY" "$CHECK" --all "$TMP/good.md" 2>&1)"
case "$out" in
  *"경고 0건"*) ok "틀을 지키고 목표가 이어진 기획서는 깨끗하다" ;;
  *)            bad "잘 쓴 기획서에 경고가 났다: $out" ;;
esac
"$PY" "$CHECK" "$TMP/good.md" >/dev/null 2>&1 && ok "깨끗하면 0으로 끝난다" || bad "깨끗한데 1로 끝났다"

# --- 연결을 끊는다. 하나씩 다른 방식으로.
sed -e 's/분야: 서비스·웹/분야: 미정/' \
    -e 's/^- \[M1.1\].*/- [M2.1] 1분기 안에 동의어 사전을 만든다 — 기준: 300쌍/' \
    -e 's/^- \[S1.1.1\].*/- [S1.1.1] 실패 로그를 본다/' \
    -e 's/검색 실패 로그 보기 — 위한 목표: S1.1.1/검색 실패 로그 보기/' \
    -e 's/동의어 사전 관리 화면 — 위한 목표: M1.1/동의어 사전 관리 화면 — 위한 목표: M9.9/' \
    "$TMP/good.md" | grep -v "타당성·경쟁력 검토" > "$TMP/bad.md"

out="$("$PY" "$CHECK" --all "$TMP/bad.md" 2>&1)"
check_code() { case "$out" in *"[$1]"*) ok "걸림: $1 — $2" ;; *) bad "안 걸림: $1 ($2)" ;; esac; }
check_code orphan-goal      "M2.1 의 부모 L2 가 없다"
check_code unmeasured-goal  "S1.1.1 에 숫자도 기준도 없다"
check_code unlinked-feature "어느 목표를 위한 기능인지 없다"
check_code unknown-goal     "M9.9 를 가리키지만 정의되지 않았다"
check_code missing-section  "타당성·경쟁력 검토 절을 지웠다"
check_code no-domain        "분야가 미정이다"
check_code childless-goal   "L1 아래 중기 목표가 사라졌다"

"$PY" "$CHECK" "$TMP/bad.md" >/dev/null 2>&1 && bad "경고가 있는데 0으로 끝났다" || ok "경고가 있으면 1로 끝난다"

# --- 빈 틀을 그대로 내면 비었다고 알려야 한다
out="$("$PY" "$CHECK" "$REPO/skills/planner/assets/plan-template.md" 2>&1)"
case "$out" in *empty-section*) ok "틀만 복사한 기획서는 비었다고 알린다" ;; *) bad "빈 틀을 통과시켰다" ;; esac
case "$out" in *no-domain*)     ok "틀의 분야 목록을 '고른 것'으로 보지 않는다" ;; *) bad "자리표시 안의 분야 목록을 선택으로 셌다" ;; esac

echo
if [ "$fails" -eq 0 ]; then
  echo "all planner checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
