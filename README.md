# kl-skills

스킬과 훅을 한 덩어리로 묶은 Claude Code 플러그인.
**설치하면 훅까지 같이 걸린다** — 설치받는 컴퓨터에서 `settings.json`을 손댈 필요가 없다.

## 설치

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

끝. Rust도, 인터넷 추가 다운로드도 필요 없다 — Rust 훅은 실행파일로 리포 안에 들어 있다.
(Python 훅을 쓰는 규칙은 설치받는 컴퓨터에 `python3` 가 있어야 돈다. 아래 "훅을 어떤 언어로 쓸까" 참고.)

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

문서만 고쳤다면 올리지 않아도 된다 — 설치본은 README를 읽지 않는다.

## 지원 환경

| 컴퓨터 | 실행파일 |
|---|---|
| 맥 (M1 이후) | `bin/kl-gate-aarch64-apple-darwin` |
| 맥 (인텔) | `bin/kl-gate-x86_64-apple-darwin` |
| 리눅스 x86_64 · WSL | `bin/kl-gate-x86_64-unknown-linux-musl` |
| 리눅스 ARM (라즈베리파이 등) | `bin/kl-gate-aarch64-unknown-linux-musl` |
| 윈도우 | `bin/kl-gate-x86_64-pc-windows-msvc.exe` |

Python 훅은 빌드가 없으므로 환경을 가리지 않지만, **그 컴퓨터에 `python3` 가 깔려 있어야** 돈다.
없으면 그 훅만 조용히 통과한다. Rust 훅은 영향받지 않는다.

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
  run.sh             mac·리눅스: Python 훅이 있으면 그걸, 없으면 Rust 실행파일을 고름
  run.ps1            윈도우용 같은 역할
  py/<게이트>.py      Python 훅. 파일을 두면 그 게이트는 Python으로 돈다
crates/kl-gate/      Rust 훅 본체. 모든 게이트를 `match` 하나로 처리
bin/                 빌드된 실행파일 — CI가 채운다. 손으로 넣지 않는다
scripts/             리포 유지용 스크립트
  bench-hook-startup.py  Rust 훅 vs Python 훅 시작 시간 측정
results/             측정 결과. 파일명에 환경·n·날짜를 넣어 덮어쓰지 않는다
tests/selftest*.sh   셀프테스트. CI가 이 패턴 전부를 돌린다
  selftest.sh            run.sh 가 실행파일·인터프리터를 제대로 고르는지
  selftest-new-topic.sh  위키 주제 생성 스크립트가 덮어쓰지 않는지
.github/workflows/build.yml   5종 빌드 → bin/ 에 자동 커밋
```

## 훅을 어떤 언어로 쓸까

Rust만 쓰지 않는다. 갈리는 지점은 **설치받는 컴퓨터에 뭐가 있어야 하는가**와
**그 훅이 얼마나 자주 도는가** 두 가지다.

| | Rust | Python |
|---|---|---|
| 설치받는 컴퓨터에 필요한 것 | 없음 (실행파일이 리포에 있음) | `python3` |
| 윈도우 | 됨 | 대개 안 깔려 있음 |
| 고치고 확인 | CI 빌드 약 1분 | 즉시 |
| 훅 한 번 시작 시간 | 4.5 ms | 32.0 ms |

시작 시간은 이 맥에서 실제로 쟀다 — 중앙값, 각 30회. 재는 방법과 결과는
`scripts/bench-hook-startup.py` 와 `results/hook-startup_macos-arm64_n30_20261111.txt`.
둘 다 프로세스를 띄우는 비용을 똑같이 포함하므로, **의미 있는 건 차이인 27.5 ms** 다.
다른 컴퓨터·다른 Python 버전에서는 달라지니, 궁금하면 그 컴퓨터에서 다시 돌려보면 된다.

27.5 ms가 문제가 되는 이유: `PreToolUse` 는 **도구를 쓸 때마다** 돈다. Bash를 100번 쓰면
100번 돌아서 약 2.8초가 쌓인다. 반대로 `SessionStart`·`Stop` 은 세션당 한 번이라
27.5 ms는 체감되지 않는다.

- **Python** — 세션당 몇 번만 도는 훅(`SessionStart`, `Stop`, `SubagentStop`),
  텍스트·JSON을 많이 다루는 규칙, 일단 만들어보고 싶을 때
- **Rust** — 모든 도구 호출마다 도는 훅(`PreToolUse`, `PostToolUse`),
  윈도우에서 반드시 돌아야 하는 규칙

Python으로 시작해서 느리면 Rust로 옮기는 게 기본 경로다. `hooks.json` 은 안 고쳐도 된다 —
`.py` 를 지우면 그때부터 Rust 쪽이 처리한다.

## 개발

### Python 훅 추가하기

1. `hooks/py/<게이트이름>.py` 를 만든다. 게이트 이름이 `argv[1]` 로 들어오고,
   사건 내용(JSON)이 표준입력으로 들어온다
2. `hooks/hooks.json` 에 그 사건을 등록한다 — 명령은 Rust와 **똑같이** `run.sh <게이트이름>`
3. 푸시하면 끝. 빌드 없음

### Rust 훅 추가하기

1. `crates/kl-gate/src/main.rs` 의 `match event` 에 분기를 추가한다
2. `hooks/hooks.json` 에 그 사건을 등록한다 (`PostToolUse`, `Stop` 등)
3. `crates/**` 를 푸시하면 CI가 5종을 다시 빌드해서 `bin/` 에 커밋한다

### 두 언어가 공유하는 규약

- 게이트 이름은 `argv[1]`, 사건 내용(JSON)은 표준입력
- 종료 코드: `0` = 통과(stdout은 모델에 전달됨), `2` = 차단(stderr가 모델에 보임)
- **판단이 안 서면 반드시 0.** 훅이 터지면 그 사건이 걸린 모든 세션이 깨진다.
  런처(`run.sh`/`run.ps1`)도 같은 원칙이라, 실행할 게 없으면 조용히 0으로 빠진다

### 로컬 빌드 (선택)

이 리포는 Rust 없이도 **쓸** 수 있다. Rust 훅을 고치려면 빌드가 필요하다:

```sh
cargo build --release                             # 현재 컴퓨터용
for t in tests/selftest*.sh; do sh "$t"; done     # 셀프테스트 전부
claude plugin validate .                          # 플러그인·스킬 형식 검사
```

5종 전부는 로컬에서 만들 수 없다(윈도우·맥 SDK 라이선스 문제). CI가 한다.

## 라이선스

MIT
