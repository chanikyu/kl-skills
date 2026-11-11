#!/bin/sh
# Checks research-to-wiki's page checker: a page written the right way is silent,
# and each omission it exists to catch is caught by name.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CHECK="$REPO/skills/research-to-wiki/scripts/check_research.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — research-to-wiki selftest skipped"
  exit 0
fi

# --- 제대로 쓴 페이지: 결론이 맨 앞, 출처마다 주소와 두 표시, 인용과 출처가 맞는다
cat > "$TMP/good.md" <<'EOF'
# 장내 미생물 불균형은 원인인가 결과인가

둘 다다. 사람에서 원인이 확인된 예는 몇 개뿐이다.

## 미생물이 원인인 쪽

- 대변 이식군 16명 중 13명이 나았다. 항생제군은 13명 중 4명이었다 [van Nood 2013].
- 염증이 생긴 장에서 대장균 무리가 불어난다 [Winter 2023, Wang 2019].

## 출처

- [van Nood 2013] 대변 이식 무작위 시험. N Engl J Med. <https://doi.org/10.1056/NEJMoa1205037> — 무작위시험 · 초록
- [Winter 2023] 염증과 장내세균과. PNAS. <https://example.org/w> — 동물실험 · 검색요약
- [Wang 2019] 질산염과 세균 증식. mBio. <https://example.org/x> — 동물실험 · 검색요약
EOF
out="$("$PY" "$CHECK" "$TMP/good.md" 2>&1)"
case "$out" in
  *"지적 0건"*) ok "제대로 쓴 페이지는 지적 0건" ;;
  *)           bad "제대로 쓴 페이지에 지적이 났다: $out" ;;
esac
"$PY" "$CHECK" "$TMP/good.md" >/dev/null 2>&1 && ok "지적이 없으면 0으로 끝난다" || bad "지적이 없는데 0이 아니다"

# --- 빠진 것마다 한 줄씩: 각 지적이 이름대로 걸리는가
cat > "$TMP/bad.md" <<'EOF'
# 원인인가 결과인가

- 목록부터 시작한다 [Kim 2020].
- 출처에 없는 인용 [Lee 2021].

## 출처

- [Kim 2020] 주소가 없는 출처. — 무작위시험 · 초록
- [Park 2019] 표시가 없는 출처. <https://example.org/p>
- [Choi 2018] 이름이 틀린 출처. <https://example.org/c> — 쥐실험 · 대충읽음
EOF
out="$("$PY" "$CHECK" "$TMP/bad.md" 2>&1)"
for code in conclusion-not-first source-missing-link source-missing-levels unknown-evidence-level \
            unknown-reading-level citation-without-source source-not-cited; do
  case "$out" in
    *"[$code]"*) ok "걸림: $code" ;;
    *)           bad "안 걸림: $code" ;;
  esac
done
"$PY" "$CHECK" "$TMP/bad.md" >/dev/null 2>&1 && bad "지적이 있는데 0으로 끝났다" || ok "지적이 있으면 1로 끝난다"
"$PY" "$CHECK" --exit-zero "$TMP/bad.md" >/dev/null 2>&1 && ok "--exit-zero 는 0으로 끝난다" || bad "--exit-zero 인데 1이다"

# --- 출처 절이 아예 없는 페이지
printf '# 제목\n\n결론이다 [Kim 2020].\n' > "$TMP/nosrc.md"
case "$("$PY" "$CHECK" "$TMP/nosrc.md" 2>&1)" in
  *"[missing-sources]"*) ok "걸림: missing-sources" ;;
  *)                     bad "출처 절이 없는데 안 잡았다" ;;
esac

# --- 이름 목록은 데이터 파일에서 온다: 코드에 박혀 있지 않다
grep -q "무작위시험" "$CHECK" && bad "근거 수준 이름이 코드에 박혀 있다" || ok "근거 수준 이름은 데이터 파일에서 읽는다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all research-to-wiki checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
