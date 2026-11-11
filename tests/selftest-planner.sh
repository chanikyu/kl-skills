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

# --- 계획 이탈: 진행 기록과 git 커밋을 섞은 실제 저장소. 이탈을 종류별로 하나씩 넣는다.
DRIFT="$REPO/skills/planner/scripts/check_drift.py"
PROJ="$TMP/proj"; mkdir -p "$PROJ"
day() { "$PY" -c "import datetime,sys; print((datetime.date.today()-datetime.timedelta(days=int(sys.argv[1]))).isoformat())" "$1"; }
D1=$(day 1); D3=$(day 3); PAST=$(day 40)
cat > "$PROJ/plan.md" <<EOF
# 검색 개선

## 1-2. 목표·타깃 설정

- [L1] 첫 검색 성공률 80% — 기준: 로그
- [L2] 검색 속도 1초 이내 — 기준: 측정
- [M1.1] 동의어 300쌍 — 기준: 300쌍
- [S1.1.1] 실패 로그 100건 분류 — 기준: $PAST 까지

## 3. 진행 기록

- [$D3] S1.1.1 실패 로그 40건 분류
- [$D3] (계획 밖) 로그인 장애 긴급 수정 — 이유: 운영 장애
- [$D1] 회의록 정리
- [$D1] M9.9 뭔가 했다
EOF
git -C "$PROJ" init -q
git -C "$PROJ" config user.name "tester"; git -C "$PROJ" config user.email "t@example.invalid"
commit_on() { GIT_AUTHOR_DATE="$1T12:00:00" GIT_COMMITTER_DATE="$1T12:00:00" \
              git -C "$PROJ" commit -q --allow-empty -m "$2"; }
git -C "$PROJ" add plan.md
commit_on "$D3" "S1.1.1 실패 로그 분류 스크립트"
commit_on "$D1" "README 오타"

# 손으로 돌리는 전체 분석: 계획 밖 일을 하나하나 보여준다
out="$("$PY" "$DRIFT" --all "$PROJ/plan.md" 2>&1)"
drift_has() { case "$out" in *"$1"*) ok "이탈: $2" ;; *) bad "놓침: $2 ($1)" ;; esac; }
drift_has "회의록 정리"        "목표 번호 없는 진행 기록을 계획 밖으로 잡는다"
drift_has "README 오타"        "목표 번호 없는 커밋을 계획 밖으로 잡는다"
# 커밋 직후 모드: 방금 커밋을 맨 앞에 따로 알린다
latest="$("$PY" "$DRIFT" --all --latest-commit "$PROJ/plan.md" 2>&1)"
case "$latest" in *"방금 커밋"*) ok "이탈: 마지막 커밋이 계획 밖이면 맨 앞에 따로 알린다" ;; *) bad "방금 커밋 알림이 없다: $latest" ;; esac
drift_has "[unknown-goal]"     "없는 목표 M9.9 를 가리킨 일을 잡는다"
drift_has "[overdue-goal]"     "기한이 지났는데 완료가 없는 목표를 잡는다"
drift_has "[drifting]"         "계획 안 비율이 기준보다 낮다고 알린다"
drift_has "L2 아래로 한 일이 없다" "손 안 댄 장기 목표를 알린다"
case "$out" in
  *"계획 안 1건"*) ok "같은 날 같은 목표의 진행 기록과 커밋을 한 건으로 센다" ;;
  *)               bad "같은 일을 두 번 셌다: $out" ;;
esac
case "$out" in
  *"로그인 장애"*"어느 목표"*|*"어느 목표"*"로그인 장애"*) bad "이유를 밝힌 계획 밖 일을 이탈로 셌다" ;;
  *)                                                       ok "'(계획 밖)' 과 이유를 쓴 일은 이탈로 세지 않는다" ;;
esac

# --- '완료' 를 적으면 기한 지난 목표가 사라져야 한다
printf -- '- [%s] S1.1.1 완료\n' "$D1" >> "$PROJ/plan.md"
out="$("$PY" "$DRIFT" --all "$PROJ/plan.md" 2>&1)"
case "$out" in *overdue-goal*) bad "완료를 적었는데 아직 기한 지남으로 본다" ;; *) ok "완료를 적으면 기한 지남이 사라진다" ;; esac

# --- 커밋을 보지 않으면 커밋 쪽 이탈은 없어야 한다
out="$("$PY" "$DRIFT" --all --no-git "$PROJ/plan.md" 2>&1)"
case "$out" in *"README 오타"*) bad "--no-git 인데 커밋을 읽었다" ;; *) ok "--no-git 이면 커밋을 보지 않는다" ;; esac

# --- 이탈 훅, 계획서를 쓸 때: 목표가 정의된 문서를 쓰면 구조와 이탈을 같이 알린다
export CLAUDE_PLUGIN_ROOT="$REPO"
out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$PROJ/plan.md" \
       | sh "$REPO/hooks/run.sh" plan-drift 2>/dev/null)"
printf '%s' "$out" | "$PY" -c "import json,sys; d=json.load(sys.stdin)['hookSpecificOutput']; assert d['hookEventName']=='PostToolUse'; assert 'off-plan-work' in d['additionalContext']" 2>/dev/null \
  && ok "계획서를 쓰면 이탈을 모델에게 닿는 모양으로 알린다" \
  || bad "계획서를 썼는데 이탈 알림이 없거나 JSON 이 아니다: $out"

out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$TMP/good.md" \
       | sh "$REPO/hooks/run.sh" plan-drift 2>/dev/null)"
[ -z "$out" ] && ok "깨끗한 계획서에는 조용하다" || bad "깨끗한 계획서에 말했다: $out"

printf '# 그냥 메모\n\n목표 번호가 없는 문서.\n' > "$TMP/memo.md"
out="$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$TMP/memo.md" \
       | sh "$REPO/hooks/run.sh" plan-drift 2>/dev/null)"
[ -z "$out" ] && ok "계획서가 아닌 문서는 건너뛴다" || bad "계획서가 아닌데 검사했다: $out"

# --- 이탈 훅, 커밋했을 때 (Rust 가 부르는 경로를 직접 흉내 낸다): 방금 커밋이 계획 밖이면 알린다
out="$(printf '{"tool_input":{"command":"git commit -m x"},"cwd":"%s"}' "$PROJ" \
       | "$PY" "$REPO/hooks/py/plan-drift.py" --plain 2>/dev/null)"
case "$out" in
  *"방금 커밋"*) ok "커밋하면 저장소의 계획서를 찾아 방금 커밋의 이탈을 알린다" ;;
  *)             bad "커밋 경로에서 이탈을 못 찾았다: $out" ;;
esac

# --- 2026-11-11 실사용에서 드러난 결함들. 세션 폴더와 커밋한 폴더가 다를 때.
ELSEWHERE="$TMP/elsewhere"; mkdir -p "$ELSEWHERE"
out="$(printf '{"tool_input":{"command":"cd %s && git commit -m x"},"cwd":"%s"}' "$PROJ" "$ELSEWHERE" \
       | "$PY" "$REPO/hooks/py/plan-drift.py" --plain 2>/dev/null)"
case "$out" in *"방금 커밋"*) ok "'cd 폴더 && 커밋' 은 그 폴더의 저장소를 본다" ;; *) bad "cd 한 폴더를 안 봤다: $out" ;; esac
out="$(printf '{"tool_input":{"command":"git -C %s commit -m x"},"cwd":"%s"}' "$PROJ" "$ELSEWHERE" \
       | "$PY" "$REPO/hooks/py/plan-drift.py" --plain 2>/dev/null)"
case "$out" in *"방금 커밋"*) ok "'git -C 폴더 commit' 은 그 폴더의 저장소를 본다" ;; *) bad "-C 폴더를 안 봤다: $out" ;; esac
case "$out" in *"커밋 "*"는 어느 목표의 일인지"*) bad "커밋 직후인데 지난 커밋을 하나하나 나열했다" ;; *) ok "커밋 직후에는 방금 커밋과 요약만 낸다" ;; esac

# 틀의 자리표시만 있는 저장소: 계획서가 없는 것과 같다
TPL="$TMP/template-only"; mkdir -p "$TPL"
cp "$REPO/skills/planner/assets/plan-template.md" "$TPL/plan-template.md"
git -C "$TPL" init -q; git -C "$TPL" config user.name t; git -C "$TPL" config user.email t@example.invalid
git -C "$TPL" add plan-template.md
GIT_AUTHOR_DATE="${D1}T12:00:00" GIT_COMMITTER_DATE="${D1}T12:00:00" git -C "$TPL" commit -q -m "틀 추가"
out="$(printf '{"tool_input":{"command":"git commit -m x"},"cwd":"%s"}' "$TPL" \
       | "$PY" "$REPO/hooks/py/plan-drift.py" --plain 2>/dev/null)"
[ -z "$out" ] && ok "기획서 틀의 자리표시는 계획서로 세지 않는다" || bad "틀을 계획서로 셌다: $out"

# --- Bash 뒤 Rust 게이트: 새 바이너리일 때만 (커밋 감지는 Rust 쪽에 있다)
T="$(sh "$REPO/hooks/run.sh" --print-target)"
BIN="$REPO/bin/kl-gate-$T"
SOURCE_VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' "$REPO/crates/kl-gate/Cargo.toml" | head -1)"
BINARY_BANNER="$(printf '{}' | "$BIN" session-start 2>/dev/null)"
if [ -x "$BIN" ] && case "$BINARY_BANNER" in *"v$SOURCE_VERSION "*) true ;; *) false ;; esac; then
  out="$(printf '{"tool_input":{"command":"git -C %s commit -q -m x"},"cwd":"%s"}' "$PROJ" "$ELSEWHERE" \
         | sh "$REPO/hooks/run.sh" after-bash 2>/dev/null)"
  case "$out" in *"방금 커밋"*) ok "Bash 뒤 게이트가 'git -C 폴더 commit' 도 커밋으로 알아본다" ;; *) bad "-C 커밋을 놓쳤다: $out" ;; esac
  out="$(printf '{"tool_input":{"command":"git commit -m x"},"cwd":"%s"}' "$PROJ" \
         | sh "$REPO/hooks/run.sh" after-bash 2>/dev/null)"
  printf '%s' "$out" | "$PY" -c "import json,sys; d=json.load(sys.stdin)['hookSpecificOutput']; assert '방금 커밋' in d['additionalContext']" 2>/dev/null \
    && ok "Bash 뒤 게이트가 커밋을 알아보고 이탈을 JSON 하나로 알린다" \
    || bad "Bash 뒤 게이트의 커밋 경로: $out"
  out="$(printf '{"tool_input":{"command":"ls -la"},"cwd":"%s"}' "$PROJ" \
         | LLM_WIKI_ROOT="$TMP/no-wiki" sh "$REPO/hooks/run.sh" after-bash 2>/dev/null)"
  [ -z "$out" ] && ok "커밋이 아닌 명령에는 조용하다" || bad "커밋이 아닌데 말했다: $out"
else
  echo "skip  로컬 바이너리($BINARY_BANNER)가 소스(v$SOURCE_VERSION)보다 오래됐다 — CI 빌드 뒤 다시 돌린다"
fi

echo
if [ "$fails" -eq 0 ]; then
  echo "all planner checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
