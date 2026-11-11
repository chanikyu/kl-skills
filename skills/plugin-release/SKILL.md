---
name: plugin-release
description: Ship a change to a Claude Code plugin all the way to the installed copy, in an order that cannot be skipped - bump the version in every file that carries it, commit and push (after the person agrees), wait for CI to pass, only then update the marketplace clone and the installed plugin, and verify the installed copy (version, banner, every hook exits 0). Then tell the person to restart, because hooks load at session start, and after the restart run verify again. Use whenever a plugin's skills or hooks were changed and should reach the installed copy, and whenever someone says the plugin was restarted and asks to check it. Triggers - release, ship, publish plugin, reinstall, update the plugin, bump version, plugin update, install after CI, restarted check, 배포, 재설치, 설치본 반영, 버전 올려, 플러그인 업데이트, 다시 시작했어 확인해줘.
---

# Plugin Release

고친 내용이 설치본에 닿기까지 **조용히 끊기는 자리가 네 군데** 있다. 넷 다 에러가 아니라
"예전 것이 계속 도는" 모양이라서, 고쳤는데 안 바뀌었다고 착각하기 쉽다.

| 자리 | 증상 | 이 스킬이 막는 방법 |
|---|---|---|
| 버전을 안 올림 | `already at the latest version` | `bump` 가 버전 파일 전부를 한 번에 올린다 |
| 장터 복제본을 안 갱신함 | 푸시했는데 설치본이 옛 커밋 | `ship` 이 업데이트 전에 장터부터 갱신한다 |
| CI 가 끝나기 전에 설치함 | 버전은 새 것인데 배너가 옛 버전 | `ship` 은 CI 성공을 확인하기 전에 설치 명령을 부르지 않는다 |
| 세션을 다시 시작 안 함 | 스킬은 새 것인데 훅이 옛 것 | 끝에 재시작을 알리고, 재시작 뒤 `verify` 로 확인한다 |

세 번째가 2026-11-11 에 실제로 났다. 순서가 README 에 적혀 있었는데도 확인 없이 설치부터
해서 옛 바이너리가 설치본에 굳었다. 이유는 같은 위키 페이지(plugin-update-flow)에 있다.

## 순서

1. **버전 올리기** — `python3 scripts/release.py bump X.Y.Z`
   - `plugin.json` 과, 리포 뿌리 `version-files.txt` 에 적힌 파일(예: `Cargo.toml`)을 같이 올린다
   - 지금보다 큰 버전만 받는다. 같으면 업데이트가 아무것도 바꾸지 않는다
   - 스킬만 새로 넣었으면 가운데 자리, 고치기만 했으면 끝자리를 올린다
2. **테스트** — 리포의 테스트를 전부 돌린다. 하나라도 실패하면 여기서 멈춘다
3. **커밋·푸시** — **사람에게 묻고** 한다. 이 스킬은 커밋을 대신 하지 않는다
4. **CI 기다리고 설치** — `python3 scripts/release.py ship`
   - 푸시가 안 됐거나 커밋 안 한 변경이 있으면 멈춘다
   - CI 를 끝까지 기다린다(몇 분 걸린다 — 백그라운드로 돌린다). 실패하면 설치하지 않고 멈춘다
   - 통과하면 CI 가 만든 커밋을 받고 → 장터 갱신 → 업데이트 → `verify` 순서로 간다
   - CI 가 없는 리포만 `--no-ci` 를 쓴다
5. **재시작 안내** — 훅은 세션이 시작될 때 읽힌다. "다시 시작해야 새 훅이 돈다"고 말한다
6. **재시작 뒤 확인** — 사람이 "다시 시작했어"라고 하면 `python3 scripts/release.py verify`
   - 세션 첫 줄 배너의 버전도 같이 본다. 둘 다 새 버전이어야 끝이다

## verify 가 보는 것

- 세션이 실제로 쓰는 설치본(`installed_plugins.json` 의 `installPath`)의 버전 = 리포 버전.
  장터 복제본(`plugins/marketplaces/...`)은 보지 않는다 — 둘이 다를 수 있다
- 설치본 `hooks.json` 의 훅마다 빈 입력 `{}` 을 주고, 0으로 끝나는지와 걸린 시간
- 훅 출력에 `vX.Y.Z` 꼴 배너가 있으면 그 버전이 리포 버전과 같은지 — 다르면 옛 바이너리가
  굳은 것이다. 같은 버전 번호로는 다시 받지 않으므로, 지웠다 다시 깐다. 지우기 전에
  `~/.claude/plugins/data/<플러그인>/` 에 저장된 것이 있는지 사람에게 보여 주고 묻는다

## 보고

"완료"에는 확인한 것을 붙인다: 커밋 해시, CI 결과, 설치본 경로와 버전, 훅 몇 개가 0으로 끝났는지,
재시작이 필요한지. 빈 입력 확인은 "훅이 터지지 않는다"까지만 보여 준다 — 훅이 맞게 판정하는지는
테스트와 `hook-replay` 가 본다.
