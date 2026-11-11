# kl-skills

스킬과 훅을 한 덩어리로 묶은 Claude Code 플러그인.
**설치하면 훅까지 같이 걸린다** — 설치받는 컴퓨터에서 `settings.json`을 손댈 필요가 없다.

## 설치

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

끝. Rust도, 인터넷 추가 다운로드도 필요 없다 — 실행파일이 리포 안에 들어 있다.

설치되면 세션 시작할 때 이 줄이 뜬다:

```
KL-SKILLS GATES v<버전> — loaded, N rules enforced
```

이 줄이 안 뜨면 훅이 안 걸린 것이다. `/plugin` 으로 활성 상태를 확인한다.

## 고친 걸 설치본에 반영하려면 — 버전을 올려야 한다

`claude plugin update` 는 `plugin.json` 의 `version` 을 보고 판단한다. 버전이 그대로면
내용을 아무리 고쳐도 `already at the latest version` 이라며 **아무것도 갱신하지 않는다.**

그래서 내용을 바꿀 때마다:

1. `.claude-plugin/plugin.json` 의 `version` 을 올린다
2. `crates/kl-gate/Cargo.toml` 의 `version` 도 같은 값으로 올린다 —
   배너가 찍는 버전이 설치본 버전과 어긋나면, 배너로 "어느 버전이 깔렸나"를 확인할 수 없다
3. 푸시하고, CI가 끝난 뒤:
   ```sh
   claude plugin marketplace update kl-skills   # 리포를 다시 clone
   claude plugin update kl-skills               # 설치본 교체
   ```
4. `claude plugin details kl-skills` 로 스킬·훅 개수가 맞는지 확인한다

## 지원 환경

| 컴퓨터 | 실행파일 |
|---|---|
| 맥 (M1 이후) | `bin/kl-gate-aarch64-apple-darwin` |
| 맥 (인텔) | `bin/kl-gate-x86_64-apple-darwin` |
| 리눅스 x86_64 · WSL | `bin/kl-gate-x86_64-unknown-linux-musl` |
| 리눅스 ARM (라즈베리파이 등) | `bin/kl-gate-aarch64-unknown-linux-musl` |
| 윈도우 | `bin/kl-gate-x86_64-pc-windows-msvc.exe` |

리눅스용은 `musl`(= 필요한 부품을 실행파일 안에 다 넣는 방식)로 만들어서,
오래된 리눅스에서도 "라이브러리 버전이 안 맞는다"는 에러가 나지 않는다.
ARM 윈도우는 x86_64 실행파일을 에뮬레이션으로 돌리므로 따로 만들지 않았다.

**목록에 없는 환경**(FreeBSD, RISC-V 등)에서는 훅이 조용히 통과한다.
세션이 깨지는 것보다 규칙이 안 걸리는 게 낫다는 판단이다.

## 구조

```
.claude-plugin/
  plugin.json        플러그인 정보 + 훅 등록 위치
  marketplace.json   GitHub에서 바로 설치되게 하는 장터 정보
skills/              스킬. 한 폴더에 SKILL.md 하나
  llm-wiki-docs/     문서를 ~/llm-wiki-docs/<주제>/wiki 로 모으는 위키 규약
hooks/
  hooks.json         어떤 사건에 어떤 명령을 돌릴지 적은 표
  run.sh             mac·리눅스: CPU 보고 맞는 실행파일 고름
  run.ps1            윈도우용 같은 역할
crates/kl-gate/      훅 본체 (Rust)
bin/                 빌드된 실행파일 — CI가 채운다. 손으로 넣지 않는다
tests/selftest*.sh   셀프테스트. CI가 이 패턴 전부를 돌린다
  selftest.sh            run.sh 가 실행파일을 제대로 고르는지
  selftest-new-topic.sh  위키 주제 생성 스크립트가 덮어쓰지 않는지
.github/workflows/build.yml   5종 빌드 → bin/ 에 자동 커밋
```

## 개발

### 훅 규칙 추가하기

1. `crates/kl-gate/src/main.rs` 의 `match event` 에 분기를 추가한다
2. `hooks/hooks.json` 에 그 사건을 등록한다 (`PostToolUse`, `Stop` 등)
3. `crates/**` 를 푸시하면 CI가 5종을 다시 빌드해서 `bin/` 에 커밋한다

종료 코드 규약: `0` = 통과(stdout은 모델에 전달됨), `2` = 차단(stderr가 모델에 보임).
**판단이 안 서면 반드시 0.** 훅이 터지면 그 사건이 걸린 모든 세션이 깨진다.

### 로컬 빌드 (선택)

이 리포는 Rust 없이도 쓸 수 있다. 직접 빌드하려면:

```sh
cargo build --release                             # 현재 컴퓨터용
for t in tests/selftest*.sh; do sh "$t"; done     # 셀프테스트 전부
claude plugin validate .                          # 플러그인·스킬 형식 검사
```

5종 전부는 로컬에서 만들 수 없다(윈도우·맥 SDK 라이선스 문제). CI가 한다.

## 라이선스

MIT
