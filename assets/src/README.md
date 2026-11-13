# README 그림 다시 만들기

`assets/*.png` 세 장은 VectorCraft(벡터 그림 앱)로 그렸다. `figures.py` 가 VectorCraft 에 명령을 보내 그리고,
VectorCraft 가 저장·내보내기를 한다. 그림을 손으로 고치지 않는다 — 고칠 것은 아래 두 파일이다.

| 파일 | 담은 것 |
| --- | --- |
| `figures.py` | 배치(위치·크기)와 그리는 순서 |
| `figures.json` | 글자, 색, 글꼴 |

게이트 이름(`hooks/hooks.json`), 스킬 이름(`skills/*/`), 버전(`.claude-plugin/plugin.json`)은 저장소에서 읽는다.
그래서 게이트나 스킬이 바뀌거나 버전을 올리면 **다시 그리기만** 하면 된다. 머리 그림의 배너에 버전이 들어
있으므로 배포 때마다 다시 그린다.

| 그림 | 내용 | 크기(pt) |
| --- | --- | --- |
| `hero` | 이름, 한 줄 설명, 스킬·게이트·언어 수, 실제 설치 명령과 배너 | 1200 × 412 |
| `turn-flow` | 한 턴의 다섯 순간과 그때 도는 게이트 전부. 답을 돌려보낼 수 있는 게이트는 주황 | 1200 × 526 |
| `parts` | 메시지 → Claude Code → 스킬·훅 게이트·위키 | 1200 × 500 |

그림마다 네 파일이 있다: `<이름>.vectorcraft`(고칠 수 있는 원본), `.svg`(글자를 윤곽선으로 바꿔 글꼴이 없어도
같게 보임), `.pdf`, 그리고 README 가 쓰는 `assets/<이름>.png`(3배 해상도, 가로 3600px, 카드 밖은 투명).

## 다시 그리기

```sh
OUT="$(mktemp -d)"
/Applications/VectorCraft.app/Contents/MacOS/VectorCraft --control 7991 \
  --automation-read-root "$OUT" --automation-write-root "$OUT" &      # 그리는 동안만 켜 둔다
python3 assets/src/figures.py --port 7991 --out "$OUT"               # --only hero 처럼 한 장만도 된다
cp "$OUT"/*.png assets/ && cp "$OUT"/*.vectorcraft "$OUT"/*.svg "$OUT"/*.pdf assets/src/
```

다시 그린 뒤에는 PNG 를 직접 열어 본다. 가로 900px 로 줄여서도 본다 — README 칸 폭이 그 정도라 작은 글자가
읽히는지 거기서 판가름 난다.

## 정한 것

- 글꼴: `Inter`(본문), `JetBrains Mono`(명령·게이트 이름). 둘 다 VectorCraft 에 들어 있다
- 색: GitHub 화면과 어울리는 회색 바탕 카드, 강조는 파랑 `#0969DA`, "답을 돌려보냄"은 주황 `#BC4C00`
- 가장 작은 글자 12pt. 900px 폭에서 9px 가 된다. 11pt 는 8px 가 되어 읽기 어려웠다
- 회사 로고를 쓰지 않는다. 예전 `parts` 그림의 Claude 별 모양은 뺐다
- 그림자·흐림 효과를 쓰지 않는다. SVG 로 내보내도 어디서나 똑같이 보이게 하려는 것이다

## 검수 기록 (2026-11-13)

본 이미지는 그릴 때마다 새 폴더(`v1`~`v5`)에 내보낸 PNG 다.

| 버전 | 본 이미지 | 위치 | 본 결함 | 고친 것 | 다시 본 결과 |
| --- | --- | --- | --- | --- | --- |
| v1 | `hero.png` | 왼쪽 설명 문장 | 한 줄이라 오른쪽 터미널 밑으로 들어가 잘림 | 폭 470pt 상자에서 줄바꿈 | v2 에서 두 줄, 겹침 없음 |
| v2 | `parts.png` | 오른쪽 카드 맨 아래 줄 | 예시 이름 셋이 카드 밖으로 넘침 | 예시를 둘로 줄임 | v3 에서 카드 안 |
| v2 | `parts.png` | 세 번째 연결선 라벨 | "writes · recalls" 가 카드에 가려 "writes · re" 만 보임 | 가지 갈림 위치를 724 → 664pt 로 옮겨 라벨 자리 확보 | v3 에서 전부 보임 |
| v2 | `parts.png` | 카드 왼쪽 연결점 | 작은 원이 카드 테두리에 반쯤 가려짐 | 원을 카드 다음에 그림 | v3 에서 온전한 원 |
| v4 | `small-*.png` (900px) | 연결선 라벨, 카드 예시, 단계 아래 이벤트 이름 | 11pt 가 약 8px 로 읽기 힘듦 | 11 → 12~13pt, 칩·설명 글자도 1pt 씩 키움 | v5 900px 에서 읽힘 |
| v4 | `reopen-*.svg` 렌더 | 전체 | 내보낸 SVG 를 VectorCraft 로 다시 열어 그림 | — | 원본과 같음(글꼴 대체·잘림 없음) |
| v5 | 세 장 원본 크기·900px·부분 확대 | 전체, 화살표 끝, 칩 테두리 | 없음 | — | 최종본 |

남은 한계: 다시 열어 비교한 것은 VectorCraft 안에서다. 다른 그림 프로그램에서 SVG·PDF 가 똑같이 보이는지는 보지 않았다.
