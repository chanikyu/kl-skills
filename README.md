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
    scripts/           new-topic.sh · index-add.py · log-append.py · lint.py
  graph-doc-memory/  위키 전체를 그래프 DB 하나로 만들고 브라우저로 보여준다
    scripts/           build_graph.py (DB 생성) · open-graph.sh (빌드 후 브라우저로 열기)
    assets/viewer.html 뷰어 템플릿. 빌드할 때 데이터가 박힌 사본이 따로 생긴다
  readable-code/     이름과 주석 규칙. 코드를 쓰거나 고칠 때
    scripts/           check_code.py (파이썬 이름·설명문 검사, ast 로 정확히)
    data/              허용할 짧은 이름 · 모호하다고 볼 이름 (코드 아님)
  natural-answering/ 생략 없이 쓰는 규칙. 보고·문서·답변 전부에 적용
    scripts/           check_prose.py (기계로 잡히는 생략·어색함 검사)
    data/              판정 기준. 패턴·허용 약어·비교로 인정할 말 (코드 아님)
    references/        work-report.md (작업 보고 6단계) · document-structure.md (문서 뼈대)
hooks/
  hooks.json         어떤 사건에 어떤 명령을 돌릴지 적은 표
                     SessionStart → 배너
                     PostToolUse(Write|Edit) → wiki-index-check · wiki-graph · prose-check
                     PostToolUse(Bash) → wiki-touch
                     Stop → wiki-sync
  run.sh             mac·리눅스: Python 훅이 있으면 그걸, 없으면 Rust 실행파일을 고름
  run.ps1            윈도우용 같은 역할
  py/<게이트>.py      Python 훅. 파일을 두면 그 게이트는 Python으로 돈다
crates/kl-gate/      Rust 훅 본체. 모든 게이트를 `match` 하나로 처리
                     판단 로직은 순수 함수로 빼서 `cargo test` 로 고정
bin/                 빌드된 실행파일 — CI가 채운다. 손으로 넣지 않는다
scripts/             리포 유지용 스크립트
  bench-hook-startup.py  Rust 훅 vs Python 훅 시작 시간 측정
results/             측정 결과. 파일명에 환경·n·날짜를 넣어 덮어쓰지 않는다
tests/selftest*.sh   셀프테스트. CI가 이 패턴 전부를 돌린다
  selftest.sh            run.sh 가 실행파일·인터프리터를 제대로 고르는지
  selftest-new-topic.sh  위키 주제 생성 스크립트가 덮어쓰지 않는지
  selftest-wiki-scripts.sh  인덱스·로그·lint 스크립트가 제대로 동작하는지
  selftest-prose.sh      생략 많은 글은 걸리고 잘 쓴 글은 조용한지 (검사별로 한 줄씩)
  selftest-banner.sh     배너가 말하는 게이트 개수가 hooks.json 과 맞는지
  selftest-wiki-sync.sh  쉘로 고친 페이지(= 훅이 못 본 변경)를 세션 끝에 잡는지
  selftest-wiki-touch.sh 같은 변경을 Bash 직후에 바로 잡는지 (바이너리 필요)
  selftest-readable-code.sh 나쁜 이름·빠진 설명문을 잡고, 잘 쓴 코드는 조용한지
  selftest-graph.sh      그래프 DB 집계가 맞는지 + 뷰어가 실제로 그려지는지
                         (크롬이 있으면 헤드리스로 띄워서 노드가 그려졌는지 센다.
                          없으면 그 검사만 건너뛴다)
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
cargo test                                        # Rust 훅 판단 로직 단위 테스트
cargo build --release                             # 현재 컴퓨터용
for t in tests/selftest*.sh; do sh "$t"; done     # 셀프테스트 전부
claude plugin validate .                          # 플러그인·스킬 형식 검사
```

5종 전부는 로컬에서 만들 수 없다(윈도우·맥 SDK 라이선스 문제). CI가 한다.

## 지금 걸려 있는 훅

| 사건 | 게이트 | 하는 일 | 언어 |
|---|---|---|---|
| `SessionStart` | `session-start` | 배너 한 줄. 훅이 실제로 걸렸는지 확인용 | Rust |
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `wiki-index-check` | `~/llm-wiki-docs/<주제>/wiki/` 에 쓴 페이지가 `index.md` 에 없으면 경고. **막지 않는다** | Rust |
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `wiki-graph` | 위키 페이지를 쓰면 그래프 DB(`<루트>/.graph/`)를 다시 만든다. 위키 밖 파일이면 즉시 끝 | Python |
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `prose-check` | 위키 페이지에서 읽는 사람이 걸릴 자리(뜻 없는 용어, 기준 없는 숫자, 빠진 주어)를 알려 준다. **막지 않는다** | Python |
| `PostToolUse` (`Bash`) | `wiki-touch` | 쉘로 위키를 고쳤는지 수정 시각으로 본다. 안 바뀌었으면 몇 ms 로 끝나고, 바뀌었을 때만 `wiki-sync` 를 부른다 | Rust |
| `Stop` | `wiki-sync` | 세션당 한 번. 수정 시각을 비교해 **어떤 방법으로 쓴 변경이든** 찾아내 그래프를 맞추고 바뀐 페이지를 검사한다. **막지 않는다** | Python |

`wiki-index-check` 가 Rust인 이유: `PostToolUse` 는 파일을 쓸 때마다 돈다(위 측정 참고).
위키 밖 경로면 JSON에서 경로 하나 읽고 바로 끝낸다.

### 왜 `Stop` 게이트가 따로 있나

`PostToolUse` 는 `Write`·`Edit`·`MultiEdit` 에만 걸린다. 그런데 모델은 **파일을 Bash로도
쓴다** — heredoc(= 셸에서 여러 줄 텍스트를 파일로 쏟아 넣는 문법), `sed`, 짧은 python 스크립트. 그러면 위 세 게이트가 전부 조용히 넘어가고,
그래프는 위키보다 뒤처진 채로 남는다. 2026-11-11에 실제로 그랬다: 어떤 세션이 조사 결과를
페이지·목차·기록에 다 반영했는데, 전부 Bash로 써서 아무 게이트도 돌지 않았다.

발동 조건에 `Bash` 를 넣는 것이 당연해 보이지만 비싸다. Bash는 가장 자주 쓰는 도구이고,
사건 내용에 담겨 오는 것은 경로가 아니라 명령문이며, 그 안의 쉘 변수는 풀 수 없다.
그래서 `wiki-sync` 는 **세션당 한 번** 돌면서 파일시스템에 묻는다 — `graph.json` 보다
새 페이지가 바뀐 페이지다. 어떻게 썼는지는 묻지 않는다.

`graph.json` 이 기준점을 겸한다. 다시 만들면 그 파일의 수정 시각이 앞으로 가므로, 다음
세션은 알아서 맞는 지점과 비교한다. 따로 기록할 상태가 없다.

`wiki-graph` 와 `prose-check` 도 같은 사건에 걸리지만 Python이다. 위 표의 기준
("`PostToolUse` 는 Rust")을 일부러 어긴 자리라 이유를 적어 둔다. **두 훅이 실제로 하는 일이
둘 다 Python이다** — 그래프를 만드는 빌더와 글을 검사하는 스크립트. 게이트만 Rust로 옮기면
Python 프로세스가 사라지지 않고, 오히려 프로세스가 하나 더 붙는다.

위키 밖 경로면 게이트가 문자열 몇 개만 비교하고 바로 끝낸다. 그래서 드는 비용은 Python이 한 번
뜨는 약 32 ms 뿐이고, 그 비용도 파일을 쓸 때만 든다. 빌더와 검사기를 Rust로 옮기는 날에
게이트도 같이 옮기면 된다.

## 라이선스

MIT
