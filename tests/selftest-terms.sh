#!/bin/sh
# Checks check_terms.py: a word the field does not use is caught with the word it does use,
# in plain text and inside .pptx and .docx; mentions in backticks, lines marked "term-check: ok"
# and the glossary itself are left alone; the word pairs come from the data file, not the code.
# (2026-11-13: slides said one thing where the field — and the person's own slides — say another.)
# Every line below that spells a wrong term on purpose carries the marker.  term-check: ok
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CHECK="$REPO/skills/natural-answering/scripts/check_terms.py"
GLOSSARY="$REPO/skills/natural-answering/data/domain-terms.tsv"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — terms selftest skipped"
  exit 0
fi

run() { "$PY" "$CHECK" "$@" 2>&1; }

# --- 평문: 틀린 말을 잡고, 분야가 쓰는 말과 출처를 같이 알린다
printf 'MAG 는 stringent quality 와 medium quality 로 나눴다.\n' > "$TMP/a.md"   # term-check: ok
out="$(run "$TMP/a.md")"; code=$?
case "$out" in *"high quality"*"MIMAG"*) ok "틀린 말에 분야가 쓰는 말과 출처를 붙인다" ;; *) bad "못 잡았다: $out" ;; esac
[ "$code" -eq 1 ] && ok "찾으면 1로 끝난다" || bad "찾았는데 종료 코드 $code"
case "$out" in *"'medium quality'"*) bad "맞는 말(medium quality)까지 잡았다" ;; *) ok "맞는 말은 잡지 않는다" ;; esac
printf 'Stringent-quality MAGs only.\n' > "$TMP/b.md"   # term-check: ok
case "$(run "$TMP/b.md")" in *"high quality"*) ok "대소문자·붙임표가 달라도 잡는다" ;; *) bad "붙임표 모양을 놓쳤다" ;; esac
printf 'improves the sequence resolution of profiles\n' > "$TMP/c.txt"   # term-check: ok
case "$(run "$TMP/c.txt")" in *"taxonomic resolution"*) ok "두 번째 용어 쌍도 잡는다" ;; *) bad "sequence resolution 을 놓쳤다" ;; esac

# --- 잡지 않는 것: 백틱 안의 언급, 표시한 줄, 용어집 자체, 맞는 글
printf '틀린 표현 `stringent quality` 대신 high quality 를 쓴다.\n' > "$TMP/d.md"   # term-check: ok
out="$(run "$TMP/d.md")"; code=$?
[ "$code" -eq 0 ] && ok "백틱 안의 언급은 쓰임이 아니다" || bad "백틱 안을 잡았다: $out"
printf 'stringent quality — 설명하려고 적은 줄 (term-check: ok)\n' > "$TMP/e.md"   # term-check: ok
[ "$(run "$TMP/e.md" >/dev/null; echo $?)" -eq 0 ] && ok "'term-check: ok' 를 단 줄은 건너뛴다" || bad "표시한 줄을 잡았다"
[ "$(run "$GLOSSARY" >/dev/null; echo $?)" -eq 0 ] && ok "용어집 파일 자체는 검사하지 않는다" || bad "용어집을 잡았다"
printf 'high-quality and medium-quality MAGs at fine taxonomic resolution\n' > "$TMP/f.md"
[ "$(run "$TMP/f.md" >/dev/null; echo $?)" -eq 0 ] && ok "맞는 글에는 조용하다" || bad "맞는 글을 잡았다"
[ "$(run "$TMP/none.md" >/dev/null; echo $?)" -eq 0 ] && ok "없는 파일은 건너뛴다" || bad "없는 파일에 터졌다"

# --- 슬라이드와 문서 파일 안의 글 (둘 다 XML 을 담은 zip 이다)
"$PY" - "$TMP" <<'PYEOF'
import sys, zipfile
folder = sys.argv[1]
slide = ('<p:sld xmlns:a="a" xmlns:p="p"><a:p><a:r><a:t>Higher sequence</a:t></a:r>'
         '<a:r><a:t> resolution with long reads</a:t></a:r></a:p></p:sld>')  # term-check: ok
with zipfile.ZipFile(folder + "/deck.pptx", "w") as deck:
    deck.writestr("ppt/slides/slide2.xml", slide)
    deck.writestr("ppt/slides/slide1.xml", '<p:sld><a:p><a:r><a:t>Title</a:t></a:r></a:p></p:sld>')
body = '<w:document><w:body><w:p><w:r><w:t>stringent quality bins</w:t></w:r></w:p></w:body></w:document>'  # term-check: ok
with zipfile.ZipFile(folder + "/report.docx", "w") as doc:
    doc.writestr("word/document.xml", body)
PYEOF
out="$(run "$TMP/deck.pptx")"
case "$out" in *"slide 2"*"taxonomic resolution"*) ok ".pptx 의 슬라이드 글을 읽고 몇 번째 슬라이드인지 알린다" ;; *) bad "슬라이드를 못 읽었다: $out" ;; esac
case "$(run "$TMP/report.docx")" in *"high quality"*) ok ".docx 의 본문을 읽는다" ;; *) bad "docx 를 못 읽었다" ;; esac
# 2026-11-13 리뷰: 문단 안 줄바꿈·탭에서 낱말이 붙어 버렸고, 압축이 깨진 파일 하나가 실행 전체를 멈췄다
"$PY" - "$TMP" <<'PYEOF'
import sys, zipfile
folder = sys.argv[1]
wrapped = '<p:sld><a:p><a:r><a:t>stringent</a:t></a:r><a:br/><a:r><a:t>quality</a:t></a:r></a:p></p:sld>'  # term-check: ok
with zipfile.ZipFile(folder + "/wrapped.pptx", "w") as deck:
    deck.writestr("ppt/slides/slide1.xml", wrapped)
tabbed = '<w:document><w:p><w:r><w:t>sequence</w:t><w:tab/><w:t>resolution</w:t></w:r></w:p></w:document>'  # term-check: ok
with zipfile.ZipFile(folder + "/tabbed.docx", "w") as doc:
    doc.writestr("word/document.xml", tabbed)
with zipfile.ZipFile(folder + "/damaged.pptx", "w", zipfile.ZIP_DEFLATED) as deck:
    deck.writestr("ppt/slides/slide1.xml", "<p:sld>" + "<a:p><a:r><a:t>x</a:t></a:r></a:p>" * 400 + "</p:sld>")
raw = bytearray(open(folder + "/damaged.pptx", "rb").read())
for offset in range(60, 90):          # 압축된 본문 한가운데를 망가뜨린다(목차는 멀쩡하다)
    raw[offset] ^= 0xFF
open(folder + "/damaged.pptx", "wb").write(bytes(raw))
PYEOF
case "$(run "$TMP/wrapped.pptx")" in *"high quality"*) ok "슬라이드 문단 안 줄바꿈을 띄어쓰기로 읽는다" ;; *) bad "줄바꿈으로 갈린 용어를 놓쳤다" ;; esac
case "$(run "$TMP/tabbed.docx")" in *"taxonomic resolution"*) ok "문서 안 탭을 띄어쓰기로 읽는다" ;; *) bad "탭으로 갈린 용어를 놓쳤다" ;; esac
out="$(run "$TMP/a.md" "$TMP/damaged.pptx")"
case "$out" in *"Traceback"*) bad "압축이 깨진 .pptx 에 멈췄다" ;; *"high quality"*) ok "압축이 깨진 파일은 건너뛰고 다른 파일의 지적은 남긴다" ;; *) bad "예상 밖: $out" ;; esac
printf 'not a zip' > "$TMP/broken.pptx"
[ "$(run "$TMP/broken.pptx" >/dev/null; echo $?)" -eq 0 ] && ok "깨진 .pptx 에도 터지지 않는다" || bad "깨진 pptx 에 터졌다"

# --- 용어 쌍은 데이터 파일에서 온다 — 코드에 박혀 있지 않다
grep -qi "stringent\|sequence resolution" "$CHECK" && bad "용어가 코드에 박혀 있다" || ok "용어 쌍은 data/domain-terms.tsv 에서 읽는다"   # term-check: ok

echo
if [ "$fails" -eq 0 ]; then
  echo "all terms checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
