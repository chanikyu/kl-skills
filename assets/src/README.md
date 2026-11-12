# README 그림 다시 만들기

`assets/*.png` 세 장은 이 폴더의 HTML 을 브라우저로 그려 찍은 것이다. 훅 이름이나 설치 명령이
바뀌면 HTML 의 글자를 고치고 다시 찍는다. 찍은 그림(PNG = 사진처럼 점으로 된 그림 파일)을 손으로 고치지 않는다.

| 그림 | 원본 | 크기(CSS px) |
| --- | --- | --- |
| `hero.png` | `hero.html` — 이름, 한 줄 설명, 실제 설치 명령과 배너 | 1200 × 360 |
| `turn-flow.png` | `turn-flow.html` — 한 턴의 다섯 순간과 그때 도는 게이트 | 1200 × 300 |
| `parts.png` | `parts.html` — 메시지 → Claude Code → 스킬·훅 게이트·위키 | 1200 × 400 |

## 만든 방법

2026-11-12, `design-taste-frontend` 스킬(Leonxlnx/taste-skill)로 만들었다.

- 색과 글꼴은 그 스킬이 배정했다. `start.mjs deal --page software --trade "developer tool"` 이 내놓은 첫 번째를 썼다
  - 팔레트 `white-link-blue`: 흰 바탕, 잉크 #111111, 강조 #1a4be0
  - 글꼴 `instrument`: `Instrument Sans` + `DM Mono`. 모서리는 `sharp`
- 두 다이어그램은 그 스킬의 `assets/diagrams`(`timeline`, `lanes`)가 그렸다. 아이콘은 `icons.mjs` 로 받았다
- 머리 그림은 장식 그림 대신 실제 설치 명령과 실제 배너 문구를 보여 준다

## 다시 찍기

```sh
K=~/.claude/skills/design-taste-frontend          # npx skills add https://github.com/Leonxlnx/taste-skill --skill design-taste-frontend -g
W=$(mktemp -d) && cp assets/src/*.html "$W" && cd "$W"
mkdir -p assets/icons && cp -R $K/assets/diagrams assets/ && cp $K/assets/system.css $K/assets/system.js assets/ && cp $K/assets/icons/icon.css assets/icons/
node $K/scripts/icons.mjs fetch ui:power ui:message-square ui:file-pen ui:terminal ui:shield-check ui:book-open ui:library si:claude --out assets/icons
python3 -m http.server 5317 --bind 127.0.0.1 &      # 아이콘을 읽으려면 file:// 이 아니라 http 로 연다
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for f in hero:360 turn-flow:300 parts:400; do
  "$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=2 --virtual-time-budget=6000 \
    --screenshot="${f%%:*}.png" --window-size=1200,${f##*:} "http://127.0.0.1:5317/${f%%:*}.html"
done
kill %1
```

`turn-flow.html` 의 `"orient": "h"` 는 지우지 않는다. 지우면 낮은 높이에서 도구가 세로 배치를 고른다.
