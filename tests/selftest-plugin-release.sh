#!/bin/sh
# Checks plugin-release. The one thing it exists for: never install before CI has
# passed. So the test fakes gh (CI) and claude (installer) and checks that a failed
# CI run never reaches the installer, while a passed one does and is then verified.
set -u

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
RELEASE="$REPO/skills/plugin-release/scripts/release.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0

ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fails=$((fails + 1)); }

PY=""
for p in python3 python; do command -v "$p" >/dev/null 2>&1 && { PY="$p"; break; }; done
if [ -z "$PY" ] || ! command -v git >/dev/null 2>&1; then
  echo "skip  no python3 or git — plugin-release selftest skipped"
  exit 0
fi

# --- 가짜 플러그인 리포: plugin.json, marketplace.json, 버전 파일 목록, toml 하나, 훅 하나
PLUG="$TMP/plug"; mkdir -p "$PLUG/.claude-plugin" "$PLUG/crate" "$PLUG/hooks"
printf '{\n  "name": "demo",\n  "version": "1.2.3",\n  "description": "x"\n}\n' > "$PLUG/.claude-plugin/plugin.json"
printf '{"name": "demo-market", "plugins": [{"name": "demo", "source": "./"}]}\n' > "$PLUG/.claude-plugin/marketplace.json"
printf '[package]\nname = "demo"\nversion = "1.2.3"\n\n[dependencies]\nserde = { version = "1" }\n' > "$PLUG/crate/Cargo.toml"
printf '# 같이 올릴 파일\ncrate/Cargo.toml\n' > "$PLUG/version-files.txt"
cat > "$PLUG/hooks/hooks.json" <<'EOF'
{"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "sh \"${CLAUDE_PLUGIN_ROOT}/hooks/banner.sh\"", "timeout": 5}]}]}}
EOF
printf '#!/bin/sh\necho "DEMO v$(sed -n %s "$CLAUDE_PLUGIN_ROOT/.claude-plugin/plugin.json")"\n' \
  "'s/.*\"version\": \"\\(.*\\)\".*/\\1/p'" > "$PLUG/hooks/banner.sh"

# --- bump: 두 파일 모두 바뀌고, 의존성 줄의 version 은 건드리지 않는다
"$PY" "$RELEASE" --repo "$PLUG" bump 1.3.0 >/dev/null 2>&1
grep -q '"version": "1.3.0"' "$PLUG/.claude-plugin/plugin.json" && ok "bump 가 plugin.json 을 바꾼다" || bad "plugin.json 이 그대로다"
grep -q '^version = "1.3.0"' "$PLUG/crate/Cargo.toml" && ok "bump 가 목록의 toml 도 바꾼다" || bad "toml 이 그대로다"
grep -q 'serde = { version = "1" }' "$PLUG/crate/Cargo.toml" && ok "의존성 줄의 version 은 건드리지 않는다" || bad "의존성 줄을 바꿨다"
"$PY" "$RELEASE" --repo "$PLUG" bump 1.3.0 >/dev/null 2>&1 && bad "같은 버전으로 bump 했다" || ok "지금 버전 이하로는 bump 하지 않는다"
"$PY" "$RELEASE" --repo "$PLUG" bump v2 >/dev/null 2>&1 && bad "X.Y.Z 가 아닌 버전을 받았다" || ok "X.Y.Z 꼴이 아니면 거절한다"

# --- 버전 파일 하나가 틀리면 아무 파일도 바꾸지 않는다 (리뷰에서 재현: 반쯤 올라간 채 멈췄다)
HALF="$TMP/half"; cp -R "$PLUG" "$HALF"
printf 'crate/Cargo.toml\nnoversion.txt\n' > "$HALF/version-files.txt"; echo "no version here" > "$HALF/noversion.txt"
"$PY" "$RELEASE" --repo "$HALF" bump 1.4.0 >/dev/null 2>&1 && bad "버전 줄이 없는 파일이 있는데 성공했다" \
  || ok "버전 줄이 없는 파일이 있으면 실패한다"
grep -q '"version": "1.3.0"' "$HALF/.claude-plugin/plugin.json" && grep -q '^version = "1.3.0"' "$HALF/crate/Cargo.toml" \
  && ok "실패하면 어떤 파일도 바꾸지 않는다" || bad "실패했는데 일부 파일만 바뀌었다"

# --- 원격 저장소를 붙인다. ship 은 푸시된 커밋에서만 돈다
git init -q --bare "$TMP/origin.git"
git -C "$PLUG" init -q -b main
git -C "$PLUG" config user.name t; git -C "$PLUG" config user.email t@example.invalid
git -C "$PLUG" add -A; git -C "$PLUG" commit -q -m init
git -C "$PLUG" remote add origin "$TMP/origin.git"; git -C "$PLUG" push -q -u origin main

# --- 가짜 gh / claude: 부른 것을 기록에 남긴다. CI 결과는 FAKE_CI 로 정한다
BIN="$TMP/bin"; mkdir -p "$BIN"; CALLS="$TMP/calls.log"
cat > "$BIN/gh" <<'EOF'
#!/bin/sh
echo "gh $*" >> "$CALLS"
case "$1 $2" in
  "run list")  if [ -n "${FAKE_RUN_LIST:-}" ]; then echo "$FAKE_RUN_LIST"; else echo '[{"databaseId": 42}]'; fi ;;
  "run watch") [ "$3" = "${FAKE_FAIL_ID:-none}" ] && { echo "build failed"; exit 1; }
               [ "$FAKE_CI" = "pass" ] && exit 0; echo "build failed"; exit 1 ;;
esac
EOF
cat > "$BIN/claude" <<'EOF'
#!/bin/sh
echo "claude $*" >> "$CALLS"
[ -n "${FAKE_SILENT:-}" ] || echo "✔ done"
EOF
chmod +x "$BIN/gh" "$BIN/claude"
export CALLS PATH="$BIN:$PATH"
printf '{"plugins": {"demo@demo-market": [{"installPath": "%s"}]}}\n' "$PLUG" > "$TMP/installed.json"
export PLUGIN_RELEASE_INSTALLED_PLUGINS="$TMP/installed.json"

# --- 커밋 안 한 변경이 있으면 ship 하지 않는다
echo dirty > "$PLUG/scratch.txt"
: > "$CALLS"
"$PY" "$RELEASE" --repo "$PLUG" ship >"$TMP/dirty.log" 2>&1 && bad "작업 트리가 더러운데 ship 했다" \
  || ok "커밋 안 한 변경이 있으면 멈춘다"
rm "$PLUG/scratch.txt"

# --- CI 실패: 설치 명령(claude)을 한 번도 부르지 않는다
: > "$CALLS"
FAKE_CI=fail "$PY" "$RELEASE" --repo "$PLUG" ship >"$TMP/fail.log" 2>&1
code=$?
[ "$code" -ne 0 ] && ok "CI 가 실패하면 0이 아닌 값으로 끝난다" || bad "CI 실패인데 0으로 끝났다"
grep -q '^claude' "$CALLS" && bad "CI 가 실패했는데 설치 명령을 불렀다" || ok "CI 가 실패하면 설치하지 않는다"
grep -q "설치하지 않는다" "$TMP/fail.log" && ok "왜 멈췄는지 말한다" || bad "멈춘 이유가 없다: $(cat "$TMP/fail.log")"

# --- CI 통과: 장터 갱신 → 업데이트 순서로 부르고, 설치본을 확인한다
: > "$CALLS"
FAKE_CI=pass "$PY" "$RELEASE" --repo "$PLUG" ship >"$TMP/pass.log" 2>&1
code=$?
order="$(grep '^claude' "$CALLS" | tr '\n' '|')"
case "$order" in
  "claude plugin marketplace update demo-market|claude plugin update demo@demo-market|") ok "CI 통과 뒤 장터 갱신 → 업데이트 순서로 부른다" ;;
  *) bad "설치 명령 순서가 틀렸다: $order" ;;
esac
[ "$code" -eq 0 ] && ok "설치본 버전과 배너가 맞으면 0으로 끝난다" || bad "확인이 실패했다: $(cat "$TMP/pass.log")"
grep -q "DEMO v1.3.0" "$TMP/pass.log" && ok "확인 단계에서 훅을 실제로 돌린다" || bad "훅을 안 돌렸다"

# --- 설치 명령이 아무것도 출력하지 않아도 끝까지 간다 (리뷰에서 재현: 빈 출력에 터졌다)
: > "$CALLS"
FAKE_CI=pass FAKE_SILENT=1 "$PY" "$RELEASE" --repo "$PLUG" ship >"$TMP/silent.log" 2>&1
grep -q '^claude plugin update' "$CALLS" && ok "설치 명령이 조용해도 업데이트까지 부른다" \
  || bad "출력 없는 장터 갱신 뒤에 멈췄다: $(tail -3 "$TMP/silent.log")"

# --- 커밋 하나에 CI 가 둘이면 둘 다 통과해야 설치한다
: > "$CALLS"
FAKE_CI=pass FAKE_RUN_LIST='[{"databaseId": 1}, {"databaseId": 2}]' FAKE_FAIL_ID=2 \
  "$PY" "$RELEASE" --repo "$PLUG" ship >"$TMP/two.log" 2>&1
grep -q '^claude' "$CALLS" && bad "둘째 CI 가 실패했는데 설치했다" || ok "CI 가 여러 개면 전부 통과해야 설치한다"

# --- 설치본에 옛 바이너리가 굳은 경우: 배너 버전이 다르면 알려 준다
OLD="$TMP/old-copy"; cp -R "$PLUG" "$OLD"
printf '#!/bin/sh\necho "DEMO v1.2.3"\n' > "$OLD/hooks/banner.sh"
printf '{"plugins": {"demo@demo-market": [{"installPath": "%s"}]}}\n' "$OLD" > "$TMP/installed.json"
"$PY" "$RELEASE" --repo "$PLUG" verify >"$TMP/stale.log" 2>&1 && bad "옛 배너인데 확인을 통과시켰다" \
  || ok "배너 버전이 리포와 다르면 실패로 본다"
grep -q "굳었다" "$TMP/stale.log" && ok "옛 바이너리가 굳었다고 알려 준다" || bad "굳은 원인을 말하지 않았다"

# --- 아직 설치 안 한 경우(설치본 버전부터 다름)는 "굳었다" 가 아니라 "설치 안 됨" 이다
printf '{"plugins": {"demo@demo-market": [{"installPath": "%s"}]}}\n' "$OLD" > "$TMP/installed.json"
sed -i.bak 's/"version": "1.3.0"/"version": "1.2.3"/' "$OLD/.claude-plugin/plugin.json"
"$PY" "$RELEASE" --repo "$PLUG" verify >"$TMP/notyet.log" 2>&1
grep -q "굳었다" "$TMP/notyet.log" && bad "설치 전인데 바이너리가 굳었다고 했다" || ok "설치 전이면 굳었다고 하지 않는다"
grep -q "설치본 버전 1.2.3" "$TMP/notyet.log" && ok "설치본 버전이 다르다고 말한다" || bad "버전 차이를 말하지 않았다"

echo
if [ "$fails" -eq 0 ]; then
  echo "all plugin-release checks passed"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
