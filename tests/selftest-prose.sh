#!/bin/sh
# Checks natural-answering's prose checker and the hook that runs it.
#
# The point of the checker is to separate writing that omits things from writing
# that does not. So the test is two documents: one written the way the user
# complained about, one written the way they asked for. The first must light up,
# the second must be silent. Then each individual check gets its own line in the
# fixture, so a rule that stops firing is caught by name.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CHECK="$REPO/skills/natural-answering/scripts/check_prose.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ]; then
  echo "skip  no python3 on this machine — prose selftest skipped"
  exit 0
fi

# --- 생략이 많은 글: 검사 하나마다 한 줄씩
cat > "$TMP/bad.md" <<'EOF'
# 생략이 많은 글

cross-mapping 위험은 낮습니다. 최장 일치는 34bp입니다.

ST 는 균의 번호입니다.

결과 파일이 생성되어진다.

위키 밖 경로면 바로 끝나므로.

이것은 느립니다.

A가 더 빠릅니다.

테스트가 전부 통과했습니다.

훅은 파일을 쓸 때마다 돌면서 경로를 확인하고 위키 안쪽이면 그래프를 다시 만들고 그렇지 않으면 아무 말도 하지 않고 바로 끝내는데 이 판단이 문자열 비교 몇 번으로 끝나기 때문에 비용이 거의 없습니다.

빌더는 skills/does-not-exist/nope.py 에 있습니다.

## 표

| 항목 | 값 |
|---|---|
| 노드 | 13 |

```python
# 코드블록 안의 locus 와 생성되어진다 는 예시이므로 잡으면 안 된다
x = "taxon"
```

`locus` 처럼 인라인 코드도 마찬가지다.
EOF

# --- 같은 내용을 생략 없이 쓴 글
cat > "$TMP/good.md" <<'EOF'
# 생략 없이 쓴 글

한 종의 DNA 조각을 다른 종의 것으로 착각할 위험(= cross-mapping)은 낮습니다.

유전자 자리(= 유전자가 놓인 위치) 294쌍을 비교했습니다.

가장 긴 완전일치는 34글자였습니다. 기계가 읽는 토막 하나가 100글자이므로, 그보다 훨씬 짧습니다.

아래 표는 노드와 링크가 몇 개인지 보여줍니다.

| 항목 | 값 |
|---|---|
| 노드 | 13 |

테스트는 41개 중 41개가 통과했습니다.
EOF

# --- 나쁜 글에서 각 검사가 이름대로 걸리는가
out="$("$PY" "$CHECK" --all "$TMP/bad.md" 2>&1)"
for code in undefined-term undefined-acronym pattern missing-comparison missing-count \
            long-sentence table-without-lead-in number-without-baseline missing-path; do
  case "$out" in
    *"[$code]"*) ok "걸림: $code" ;;
    *)           bad "안 걸림: $code" ;;
  esac
done

# --- 코드블록·인라인 코드는 글이 아니다
case "$out" in
  *"'taxon'"*) bad "코드블록 안의 용어를 잡았다" ;;
  *)           ok "코드블록 안은 건너뛴다" ;;
esac
hits=$(printf '%s' "$out" | grep -c "locus" || true)
[ "$hits" -eq 0 ] && ok "인라인 코드 안은 건너뛴다" || bad "인라인 코드 안의 용어를 잡았다($hits건)"

# --- 잘 쓴 글은 조용해야 한다. 여기서 소리가 나면 검사가 쓸모없다
good="$("$PY" "$CHECK" "$TMP/good.md" 2>&1)"
case "$good" in
  *"경고 0건"*) ok "생략 없이 쓴 글은 경고 0건" ;;
  *)            bad "잘 쓴 글에 경고가 났다: $good" ;;
esac

# --- 종료 코드: 경고가 있으면 1, --exit-zero 면 0 (훅은 세션을 깨면 안 된다)
"$PY" "$CHECK" "$TMP/bad.md" >/dev/null 2>&1 && bad "경고가 있는데 0으로 끝났다" \
  || ok "경고가 있으면 1로 끝난다"
"$PY" "$CHECK" --exit-zero "$TMP/bad.md" >/dev/null 2>&1 && ok "--exit-zero 는 0으로 끝난다" \
  || bad "--exit-zero 인데 1로 끝났다"

# --- 판정 기준은 데이터 파일에서 온다: 용어를 등록하면 그 경고가 사라져야 한다
cp -R "$REPO/skills/natural-answering/data" "$TMP/data"
printf 'cross-mapping\n' >> "$TMP/data/known-terms.txt"
out2="$("$PY" "$CHECK" --data-dir "$TMP/data" "$TMP/bad.md" 2>&1)"
case "$out2" in
  *"'cross-mapping'"*) bad "등록한 용어를 아직도 경고한다 — 데이터 파일이 안 읽힌다" ;;
  *)                   ok "등록한 용어는 경고하지 않는다" ;;
esac

# --- 훅: 위키 페이지면 경고를 보여주고, 그 밖이면 아무 말도 하지 않는다
mkdir -p "$TMP/wiki-root/topic-a/wiki"
cp "$TMP/bad.md" "$TMP/wiki-root/topic-a/wiki/page.md"
cp "$TMP/bad.md" "$TMP/wiki-root/topic-a/wiki/index.md"
cp "$TMP/good.md" "$TMP/wiki-root/topic-a/wiki/clean.md"
export LLM_WIKI_ROOT="$TMP/wiki-root"
hook() { printf '%s' "$1" | sh "$REPO/hooks/run.sh" prose-check 2>/dev/null; }
payload() { printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$1"; }

out="$(hook "$(payload "$TMP/wiki-root/topic-a/wiki/page.md")")"
case "$out" in
  *natural-answering*) ok "훅이 위키 페이지를 검사했다" ;;
  *)                   bad "훅이 위키 페이지에서 아무 말도 안 했다" ;;
esac

out="$(hook "$(payload "$TMP/wiki-root/topic-a/wiki/clean.md")")"
[ -z "$out" ] && ok "잘 쓴 페이지에는 조용하다" || bad "잘 쓴 페이지에 말을 했다: $out"

out="$(hook "$(payload "$TMP/wiki-root/topic-a/wiki/index.md")")"
[ -z "$out" ] && ok "index.md 는 건너뛴다(목차는 문장이 아니다)" || bad "index.md 를 검사했다"

out="$(hook "$(payload "$TMP/bad.md")")"
[ -z "$out" ] && ok "위키 밖 파일은 건너뛴다" || bad "위키 밖 파일을 검사했다: $out"

hook 'not json' >/dev/null 2>&1 && ok "깨진 입력에도 0으로 끝난다" || bad "깨진 입력에 터졌다"
hook '' >/dev/null 2>&1 && ok "빈 입력에도 0으로 끝난다" || bad "빈 입력에 터졌다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all prose checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
