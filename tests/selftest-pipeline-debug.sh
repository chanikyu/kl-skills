#!/bin/sh
# Checks probe.py, the helper that turns "what did this stage output" into numbers.
#
# The fixture is a tiny three-stage pipeline where stage two silently introduces
# empty cells — the kind of fault that surfaces three stages later as a KeyError.
# The point of the probe is that stage two looks different from stage one in its
# numbers, so the first broken stage is visible without guessing.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PROBE="$REPO/skills/pipeline-debug/scripts/probe.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 — pipeline-debug selftest skipped"
  exit 0
fi

# --- 세 단계 파이프라인. 2단계에서 메타데이터가 없는 샘플의 site 가 비고, 한 행은 열이 모자란다.
printf 'sample\tdepth\nS1\t30\nS2\t12\nS3\t45\n'                 > "$TMP/stage1_loaded.tsv"
printf 'sample\tdepth\tsite\nS1\t30\tgut\nS2\t12\t\nS3\t45\n'     > "$TMP/stage2_merged.tsv"
printf 'sample\tdepth\tsite\nS1\t30\tgut\nS3\t45\tNA\n'           > "$TMP/stage3_filtered.tsv"

out1="$("$PY" "$PROBE" "$TMP/stage1_loaded.tsv")"
out2="$("$PY" "$PROBE" "$TMP/stage2_merged.tsv")"
case "$out1" in *"빈 칸: 없음"*) ok "1단계는 빈 칸이 없다고 보여준다" ;; *) bad "1단계: $out1" ;; esac
case "$out2" in *"site 1개"*)   ok "2단계에서 처음 생긴 빈 칸을 열 이름과 함께 보여준다" ;; *) bad "2단계 빈 칸: $out2" ;; esac
case "$out2" in *"열 개수가 머리줄과 다른 행: 1개"*) ok "열이 모자란 행을 센다" ;; *) bad "열 개수 불일치를 놓쳤다" ;; esac
case "$out1" in *"행 3개 × 열 2개"*) ok "행과 열 개수를 센다" ;; *) bad "개수: $out1" ;; esac
out3="$("$PY" "$PROBE" "$TMP/stage3_filtered.tsv")"
case "$out3" in *"site 1개"*) ok "NA 도 빈 칸으로 센다" ;; *) bad "NA 를 값으로 셌다: $out3" ;; esac

# --- 서열 파일: 여러 줄로 감긴 서열과, 서열이 빈 레코드
printf '>seqA desc\nACGT\nACGT\n>seqB\n>seqC\nAC\n' > "$TMP/reads.fasta"
out="$("$PY" "$PROBE" "$TMP/reads.fasta")"
case "$out" in *"레코드 3개"*)             ok "서열 레코드를 센다" ;; *) bad "레코드 수: $out" ;; esac
case "$out" in *"최소 0, 최대 8, 합 10"*)  ok "여러 줄 서열의 길이를 합쳐 잰다" ;; *) bad "길이: $out" ;; esac
case "$out" in *"서열이 빈 레코드: 1개"*) ok "서열이 빈 레코드를 따로 알린다" ;; *) bad "빈 레코드를 놓쳤다" ;; esac

# --- 압축된 표도 표로 읽는다
gzip -c "$TMP/stage1_loaded.tsv" > "$TMP/stage1_loaded.tsv.gz"
out="$("$PY" "$PROBE" "$TMP/stage1_loaded.tsv.gz")"
case "$out" in *"행 3개 × 열 2개"*) ok ".gz 압축 표를 풀어서 읽는다" ;; *) bad "압축 표: $out" ;; esac

# --- JSON
printf '[{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]' > "$TMP/items.json"
out="$("$PY" "$PROBE" "$TMP/items.json")"
case "$out" in *"항목 2개"*) ok "JSON 목록의 길이와 키를 보여준다" ;; *) bad "JSON: $out" ;; esac
printf '{"broken": ' > "$TMP/broken.json"
out="$("$PY" "$PROBE" "$TMP/broken.json")"
case "$out" in *"JSON 으로 읽히지 않는다"*) ok "깨진 JSON 을 그 사실로 보고한다" ;; *) bad "깨진 JSON: $out" ;; esac

# --- 앞 단계가 아무것도 안 쓴 경우, 파일이 아예 없는 경우
: > "$TMP/empty.tsv"
out="$("$PY" "$PROBE" "$TMP/empty.tsv")"
case "$out" in *"앞 단계가 아무것도 쓰지 않았다"*) ok "빈 파일을 앞 단계의 문제로 알린다" ;; *) bad "빈 파일: $out" ;; esac
out="$("$PY" "$PROBE" "$TMP/nope.tsv")"
case "$out" in *"없다"*) ok "없는 파일을 없다고 말한다" ;; *) bad "없는 파일: $out" ;; esac

echo
if [ "$fails" -eq 0 ]; then
  echo "all pipeline-debug checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
