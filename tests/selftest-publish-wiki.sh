#!/bin/sh
# Checks publish_wiki.py --out (no network): docs/wiki is copied page for page into the shape
# the GitHub Wiki tab reads — links to other pages lose ".md", links and pictures that leave the
# wiki become full GitHub addresses, and the footer every page repeats is left to _Footer.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PUBLISH="$REPO/scripts/publish_wiki.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — publish-wiki selftest skipped"
  exit 0
fi

OUT="$TMP/wiki"
"$PY" "$PUBLISH" --out "$OUT" >/dev/null 2>&1 || bad "변환이 실패했다"

src_count="$(ls "$REPO"/docs/wiki/*.md | wc -l | tr -d ' ')"
out_count="$(ls "$OUT"/*.md 2>/dev/null | wc -l | tr -d ' ')"
[ "$src_count" -eq "$out_count" ] && ok "페이지 ${src_count}개가 모두 옮겨진다" || bad "원본 $src_count 개, 옮긴 것 $out_count 개"

# 백틱 안의 예시(`[text](page.md)`)는 링크가 아니라 글이다 — 빼고 센다
left="$(for f in "$OUT"/*.md; do sed 's/`[^`]*`//g' "$f" | grep -qE '\]\([^):#]+\.md(#[^)]*)?\)' && echo "$f"; done)"
[ -z "$left" ] && ok "다른 페이지로 가는 링크에 .md 가 남지 않는다" || bad ".md 링크가 남았다: $left"
left="$(grep -lE '(\]\(|src=")\.\./' "$OUT"/*.md 2>/dev/null)"
[ -z "$left" ] && ok "위키 밖을 가리키는 ../ 경로가 남지 않는다" || bad "../ 경로가 남았다: $left"

grep -q '](Installation)' "$OUT/Home.md" && ok "페이지 링크는 위키 페이지 이름이 된다 (Installation)" || bad "Home 의 페이지 링크가 그대로다"
grep -q 'src="https://raw.githubusercontent.com/[^"]*/assets/hero.png"' "$OUT/Home.md" \
  && ok "그림은 저장소의 원본 그림 주소를 가리킨다" || bad "그림 주소가 바뀌지 않았다"
grep -q '](https://github.com/[^)]*/blob/[^)]*/README.md)' "$OUT/_Sidebar.md" \
  && ok "위키 밖 문서는 저장소의 파일 주소가 된다" || bad "README 링크가 바뀌지 않았다"

tail -1 "$OUT/Installation.md" | grep -q "MIT licensed" && bad "페이지마다 꼬리말이 남아 _Footer 와 겹친다" \
  || ok "페이지의 꼬리말은 빼고 _Footer 하나만 쓴다"
grep -q "MIT licensed" "$OUT/_Footer.md" && ok "_Footer 는 그대로 있다" || bad "_Footer 가 비었다"

grep -q "github.com/chanikyu" "$PUBLISH" && bad "저장소 주소가 스크립트에 박혀 있다" || ok "저장소 주소는 git 설정에서 읽는다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all publish-wiki checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
