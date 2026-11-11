<div align="center">

# kl-skills

**스킬과 훅을 한 덩어리로 묶은 Claude Code 플러그인**

설치하면 훅까지 같이 걸린다 — 설치받는 컴퓨터에서 `settings.json` 을 손댈 필요가 없다.

<p>
  <img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
  <img src="https://img.shields.io/badge/macOS-arm64%20%C2%B7%20x86__64-000000?logo=apple&logoColor=white" alt="macOS" />
  <img src="https://img.shields.io/badge/Linux-arm64%20%C2%B7%20x86__64-FCC624?logo=linux&logoColor=black" alt="Linux" />
  <img src="https://img.shields.io/badge/Windows-x86__64-0078D4?logo=windows&logoColor=white" alt="Windows" />
</p>
<p>
  <img src="https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/-Rust-000000?logo=rust&logoColor=white" alt="Rust" />
  <img src="https://img.shields.io/badge/-Shell-4EAA25?logo=gnu-bash&logoColor=white" alt="Shell" />
  <img src="https://img.shields.io/badge/-Markdown-000000?logo=markdown&logoColor=white" alt="Markdown" />
</p>

</div>

## Claude Code 에 설치하기

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

세션을 다시 시작하면 바로 돈다. 요구 사항과 확인 방법은 [설치](#설치) 절에 있다.

<p align="center"><a href="#설치">설치로 건너뛰기 ↓</a></p>

# kl-skills

Claude 는 일을 잘하지만, 알게 된 것을 다음 대화로 가져가지 못하고, "쉽게 써 줘" 같은 지시는
대화가 길어지면 잊는다. `kl-skills` 는 그 빈자리를 메운다. 알게 된 것은 위키에 남겨 다음 질문 때
찾아 붙이고, 지켜야 할 규칙은 훅으로 걸어 답이 끝날 때마다 검사한다.

```text
말하기 → 위키에서 찾기 → 일하기 → 고친 것 검사 → 답 검사 → 위키에 남기기 → 배포
```

규칙을 프롬프트마다 다시 말하는 대신, 한 번 설치해서 일하는 방식의 일부로 만든다.

> 기억할 것은 위키에. 지킬 것은 훅에.

스킬(= 필요할 때 Claude 가 읽는 작업 설명서)이 방법을 알려 주고, 훅(= 정해진 순간마다 자동으로
도는 검사)이 그 방법을 지켰는지 본다. 아래 표의 개수는 `tests/selftest-readme.sh` 가 실제 저장소와
맞는지 확인한다.

| 들어 있는 것 | 개수 | 하는 일 |
| --- | --: | --- |
| 스킬 | 11개 | 위키 기록·검색·그래프, 쉬운 답변, 이름·주석 규칙, 기획, 디버깅, 배포, 문헌 조사 |
| 훅 게이트 | 9개 | 답변 검사, 위키 목차·그래프 갱신, 글·코드 검사, 계획 이탈 알림, 위키 자동 검색 |
| 셀프테스트 | 18묶음 | 훅·Rust 코드를 바꾼 커밋마다 CI(= GitHub 에서 도는 자동 테스트와 빌드)가 전부 돌린다 |
| 실행파일 | 5종 | 맥·리눅스·윈도우용. Rust 없이 설치된다 |

## 설치

> [!IMPORTANT]
> 9개 게이트 중 대부분이 Python 훅이다. 설치받는 컴퓨터에 `python3` 가 있어야 돈다.
> 없으면 그 훅들은 오류 없이 그냥 통과한다 — 설치는 됐는데 검사가 안 걸린 상태가 된다.

Claude Code 안에서:

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

첫 줄은 이 리포를 장터(= 플러그인 목록을 내려받아 두는 곳)로 등록하고, 둘째 줄이 실제로 설치한다.
Rust 도, 인터넷 추가 다운로드도 필요 없다 — Rust 훅은 실행파일로 리포 안에 들어 있다.
세션을 다시 시작하면 첫 줄에 이것이 뜬다:

```
KL-SKILLS GATES v<버전> — loaded, 9 rules enforced
```

이 줄이 안 뜨면 훅이 안 걸린 것이다. `/plugin` 으로 켜져 있는지 확인한다.

### 고친 걸 설치본에 반영하려면 — 버전을 올려야 한다

`claude plugin update` 는 `plugin.json` 의 `version` 만 보고 판단한다. 버전이 그대로면 내용을
아무리 고쳐도 `already at the latest version` 이라며 **아무것도 갱신하지 않는다.** 그래서
`plugin-release` 스킬의 순서를 따른다. 손으로 하면 순서를 건너뛰게 된다 — CI 가 끝나기 전에
설치해서 옛 바이너리가 설치본에 굳은 일이 실제로 있었다.

```sh
python3 skills/plugin-release/scripts/release.py bump X.Y.Z   # plugin.json + version-files.txt 의 파일
# 테스트 → 커밋 → 푸시
python3 skills/plugin-release/scripts/release.py ship         # CI 통과를 확인한 뒤에만 설치하고, 설치본을 확인
# 세션을 다시 시작한 뒤
python3 skills/plugin-release/scripts/release.py verify
```

`ship` 은 스킬·문서만 바꾼 커밋처럼 CI 가 애초에 돌지 않는 커밋을 알아보고, 그때는 CI 를 기다리지
않고 설치한다. `crates/kl-gate/Cargo.toml` 이 `version-files.txt` 에 있는 이유: 배너가 찍는 버전이
설치본 버전과 어긋나면, 배너로 "어느 버전이 깔렸나"를 확인할 수 없다. 문서만 고쳤다면 버전을 올리지
않아도 된다 — 설치본은 README 를 읽지 않는다.

<details>
<summary><strong>지우기 · 다시 설치하기</strong></summary>

```sh
claude plugin uninstall kl-skills@kl-skills      # 플러그인을 지운다
claude plugin marketplace update kl-skills       # 장터 복제본을 최신으로
claude plugin install kl-skills@kl-skills        # 다시 설치한다
```

지워도 남는 것:

- 위키 `~/llm-wiki-docs/` 와 그 그래프 `~/llm-wiki-docs/.graph/` — 사용자가 쌓은 지식이라 플러그인과 따로 산다
- 각 프로젝트에 쓴 계획서와 진행 기록

다시 설치해야 하는 경우는 하나다 — 설치본에 옛 바이너리가 굳었을 때. 같은 버전 번호로는 다시
받지 않으므로 업데이트로는 안 고쳐진다. `release.py verify` 가 "옛 바이너리가 굳었다"고 알려 준다.
지우기 전에 `~/.claude/plugins/data/kl-skills/` 에 남겨 둔 것이 있는지 본다.

</details>

## 시작하기

전체 목록부터 읽지 말고, 지금 하려는 일에서 시작한다. 스킬은 대화 내용이 설명과 맞으면 Claude 가
알아서 읽는다. 이름을 직접 말해도 된다.

| 하려는 일 | 이렇게 말한다 | 쓰이는 스킬 |
| --- | --- | --- |
| 알게 된 것을 남기기 | "위키에 정리해줘" | `llm-wiki-docs` |
| 위키에서 찾아 쓰기 | 따로 말할 것 없음 — 매 메시지마다 훅이 찾아 붙인다 | `wiki-recall` |
| 위키를 한눈에 보기 | "위키 그래프 보여줘" | `graph-doc-memory` |
| 문헌 조사 | "○○가 원인인지 결과인지 리서치해줘" | `research-to-wiki` |
| 기획 | "planner 로 ○○ 기획해줘" | `planner` |
| 에러 원인 찾기 | "이 에러 원인 찾아줘" | `pipeline-debug` |
| 코드 쓰기 | 따로 말할 것 없음 — 이름·주석·값 규칙이 함께 적용된다 | `readable-code`, `no-hardcoding` |
| 훅이 엉뚱하게 떴을 때 | "이 훅을 실제 대화에 다시 돌려봐" | `hook-replay` |
| 플러그인 배포 | "배포해줘" | `plugin-release` |
| 재시작 뒤 확인 | "다시 시작했어, 확인해줘" | `plugin-release` |

훅은 할 일이 없다. 대화에서 이런 모양으로 보인다:

```text
Stop hook feedback:
natural-answering: 답변을 고치고 다시 끝낼 것.
1. 파일을 고친 턴이라 작업 보고 6단계로 끝내야 한다(references/work-report.md).
   빠진 단계: 검증 결과, 문제 및 제약
```

막는 훅은 `answer-check` 하나뿐이고, 한 턴에 한 번만 막는다. 나머지는 알리기만 한다.

## 새 소식

모두 2026-11-11 에 나왔다. 전체 기록은 `git log` 에 있다.

- **0.20.x — 작업 보고 검사.** 파일을 고친 턴의 마지막 답에 작업 보고 6단계(결과·요약·변경·검증·
  제약·후속)가 없으면 막는다. 단계 이름은 `references/work-report.md` 의 표에서 읽는다.
  0.20.2 에서 README 를 지금 모양으로 바꾸고, CI 가 돌지 않는 커밋도 `ship` 할 수 있게 했다
- **0.19.0 — 스킬 셋 추가.** `hook-replay`, `plugin-release`, `research-to-wiki`. 글 검사가 인용 속
  저자 이름·학술지 약어를 용어로 잡던 것과, 위키 검색이 한 글자 낱말을 다른 낱말 속에서 찾던 것을 고쳤다
- **0.18.x — 되물음 판정.** 같은 질문을 다시 받은 경우만 막는다. 기록 속 기계 글(요약문·규칙 묶음)과
  답을 받기 전의 재전송은 되물음으로 세지 않는다
- **0.18.0 — 계획 이탈과 위키 자동 검색.** 진행 기록·커밋이 계획에서 벗어나면 알리고, 매 메시지마다
  위키를 찾아 관련 페이지를 붙인다
- **0.17.0 — `planner`.** 분야·기간·수준으로 틀을 정하고 장기 → 중기 → 단기 목표가 이어지는지 본다
- **0.16.0 — 훅 지적이 모델에게 닿게.** 그 전까지 게이트 넷의 지적이 디버그 기록에만 쌓였다
- **0.14.0 — `natural-answering` 이 답을 검사.** 답이 끝날 때마다 훅이 읽기 시작했다

## 들어 있는 것

```text
kl-skills/
|-- .claude-plugin/   # 플러그인 정보와 장터(marketplace) 정보
|-- skills/           # 스킬 11개. 한 폴더에 SKILL.md 하나
|-- hooks/            # hooks.json (어떤 사건에 무엇을 돌리나) + 런처 + Python 훅
|-- crates/kl-gate/   # Rust 훅 본체
|-- bin/              # 빌드된 실행파일 5종 — CI 가 채운다
|-- scripts/          # 리포 유지용 스크립트 (훅 시작 시간 측정)
|-- results/          # 측정 결과
|-- tests/            # 셀프테스트 18묶음
```

리포 뿌리가 정본이다. 설치본은 그 사본이고, 손으로 고치지 않는다.

### 스킬

| 스킬 | 언제 쓰나 | 하는 일 |
| --- | --- | --- |
| `llm-wiki-docs` | 알게 된 것을 남길 때 | 문서를 `~/llm-wiki-docs/<주제>/wiki/` 에 한 주제 한 페이지로 모은다. `index.md`·`log.md` 를 같이 관리한다 |
| `wiki-recall` | 매 메시지 (훅이 대신 부른다) | 위키에서 관련 페이지를 찾아 답에 쓴다. 위키가 작으면 통째로(CAG), 크면 골라서(RAG) |
| `graph-doc-memory` | "그래프 보여줘" 할 때 | 위키 전체를 그래프 DB 하나로 만들고, Obsidian 식 그래프 뷰로 브라우저에 띄운다 |
| `research-to-wiki` | 리서치·문헌 조사 | 출처마다 근거 수준(사람 시험·동물 실험…)과 읽은 수준(본문·초록)을 적게 하고, 빠지면 검사가 잡는다 |
| `natural-answering` | 사람이 읽는 모든 글 | 용어 정의·비교 기준·중간 단계를 생략하지 않게 한다. 작업 보고 6단계와 문서 뼈대도 여기 있다 |
| `readable-code` | 코드를 쓰거나 고칠 때 | 이름은 담긴 것을 따라 짓고, 주석에는 왜 그렇게 했는지를 쓴다 |
| `no-hardcoding` | 코드에 값을 적으려 할 때 | 목록·매핑·경로·임계값을 코드에 박지 않고, 이미 있는 파일에서 읽거나 데이터 파일로 뺀다 |
| `pipeline-debug` | 에러·이상한 결과 | 에러가 난 줄이 아니라, 파이프라인을 따라 처음 틀어진 단계를 찾는다 |
| `planner` | 기획할 때 | 분야·기간·수준으로 틀을 정하고 리서치 → 목표 → 명세 → 일정 순으로 쓴다. 진행이 계획에서 벗어나면 알린다 |
| `hook-replay` | 훅을 고친 뒤, 오탐이 났을 때 | 훅을 실제 대화 기록의 사람 메시지마다 다시 돌려, 그때 뭐라고 했을지 표로 남긴다 |
| `plugin-release` | 플러그인을 배포할 때 | 버전 → 커밋·푸시 → CI 통과 확인 → 설치 → 설치본 확인. 순서를 못 건너뛴다 |

### 훅 게이트

| 사건 | 게이트 | 하는 일 | 언어 |
| --- | --- | --- | --- |
| `SessionStart` | `session-start` | 배너 한 줄. 훅이 실제로 걸렸는지 확인용 | Rust |
| `UserPromptSubmit` | `wiki-recall` | 사용자가 말할 때마다 위키를 검색해 관련 페이지의 경로와 핵심 줄을 붙인다. 낱말 둘 이상이 겹치고 질문을 40% 이상 덮을 때만 붙인다 | Python |
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `wiki-index-check` | 위키에 쓴 페이지가 `index.md` 에 없으면 경고. **막지 않는다** | Rust |
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `wiki-graph` | 위키 페이지를 쓰면 그래프 DB(`<루트>/.graph/`)를 다시 만든다. 위키 밖 파일이면 즉시 끝 | Python |
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `prose-check` | 위키 페이지에서 읽는 사람이 걸릴 자리(뜻 없는 용어, 기준 없는 숫자, 빠진 주어)를 알려 준다. **막지 않는다** | Python |
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `code-check` | 쓴 `.py` 파일의 이름과 설명문을 바로 지적한다. 캐시·가상환경·임시 경로는 건너뛴다. **막지 않는다** | Python |
| `PostToolUse` (`Write\|Edit\|MultiEdit`) | `plan-drift` | 목표 번호가 정의된 계획서를 쓰면 틀과 이탈을 같이 알린다. **막지 않는다** | Python |
| `PostToolUse` (`Bash`) | `after-bash` | Bash 뒤에 두 가지를 본다 — 쉘로 위키를 고쳤나, 커밋했나. 커밋이면 계획 이탈을 알린다. 한 게이트로 묶어 런처 비용을 한 번만 낸다 | Rust |
| `Stop` | `wiki-sync` | 세션당 한 번. **어떤 방법으로 쓴 변경이든** 찾아내 그래프를 맞추고 바뀐 페이지를 검사한다. **막지 않는다** | Python |
| `Stop` | `answer-check` | 방금 한 답변을 읽는다. 답이 빗나가 사람이 다시 물었거나, 파일을 고친 턴인데 작업 보고 6단계가 없거나, 답이 화면 하나를 넘거나, 글 검사에 걸리면 **한 번 막는다**. 두 번은 막지 않는다 | Python |

<details>
<summary><strong>파일별 설명</strong></summary>

```text
.claude-plugin/
  plugin.json        플러그인 정보 + 훅 등록 위치
  marketplace.json   GitHub 에서 바로 설치되게 하는 장터 정보
skills/
  llm-wiki-docs/     문서를 ~/llm-wiki-docs/<주제>/wiki 로 모으는 위키 규약
    scripts/           new-topic.sh · index-add.py · log-append.py · lint.py
  graph-doc-memory/  위키 전체를 그래프 DB 하나로 만들고 브라우저로 보여준다
    scripts/           build_graph.py (DB 생성) · open-graph.sh (빌드 후 브라우저로 열기)
    assets/viewer.html 뷰어 템플릿. 빌드할 때 데이터가 박힌 사본이 따로 생긴다
  no-hardcoding/     값·목록·매핑·경로·임계값을 코드에 박지 않게
  pipeline-debug/    에러가 나면 파이프라인을 따라 처음 틀어진 단계를 찾는다
    scripts/           probe.py (단계 사이 파일의 개수·열·빈 칸·앞부분을 숫자로)
  planner/           분야·기간·수준으로 틀을 정하고 리서치 → 목표 → 명세 → 일정으로 기획
    references/        domains.md (여덟 분야의 출발 질문·산출물·분석 틀·함정)
    assets/            plan-template.md (기획서 틀)
    scripts/           check_plan.py (빠진 단계, 부모 없는 목표, 기준 없는 목표, 목표 없는 기능)
                       check_drift.py (진행 기록·커밋이 계획에서 벗어나는지)
    data/              필수 절 목록 · 분야 이름
  wiki-recall/       위키에서 찾아 답에 쓴다. 작으면 통째로(CAG), 크면 골라서(RAG)
    scripts/           recall.py (두 글자 조각 + BM25 + 질문을 덮는 비율 + 그래프 이웃)
    data/              말버릇 낱말 · 조사 · 흔한 조각 (코드 아님)
  readable-code/     이름과 주석 규칙. 코드를 쓰거나 고칠 때
    scripts/           check_code.py (파이썬 이름·설명문 검사, ast 로 정확히)
    data/              허용할 짧은 이름 · 모호하다고 볼 이름 (코드 아님)
  natural-answering/ 생략 없이 쓰는 규칙. 보고·문서·답변 전부에 적용
    scripts/           check_prose.py (기계로 잡히는 생략·어색함 검사)
    data/              판정 기준. 패턴·허용 약어·되묻는 말투 (코드 아님)
    references/        work-report.md (작업 보고 6단계) · document-structure.md (문서 뼈대)
  hook-replay/       훅을 실제 대화 기록의 사람 메시지마다 다시 돌려 오탐·놓침을 찾는다
    scripts/           replay.py (시점별로 기록을 잘라 훅에 넘기고 결과를 TSV 로)
  plugin-release/    버전 → 커밋·푸시 → CI 통과 확인 → 설치 → 설치본 확인
    scripts/           release.py (bump · ship · verify)
  research-to-wiki/  문헌 조사를 위키로. 출처마다 근거 수준·읽은 수준을 적게 하고 검사한다
    scripts/           check_research.py (결론이 맨 앞인가, 출처 표시·인용 짝이 맞나)
    data/              근거 수준 · 읽은 수준 이름 (코드 아님)
    assets/            research-page-template.md (조사 페이지 틀)
hooks/
  hooks.json         어떤 사건에 어떤 명령을 돌릴지 적은 표
  run.sh             mac·리눅스: Python 훅이 있으면 그걸, 없으면 Rust 실행파일을 고름
  run.ps1            윈도우용 같은 역할
  py/<게이트>.py      Python 훅. 파일을 두면 그 게이트는 Python 으로 돈다
  py/_transcript.py  대화 기록에서 사람 메시지와 이번 턴의 도구 호출을 읽는다 (answer-check · hook-replay)
  py/_work_files.py  사용자 작업 파일과 임시 경로를 가른다 (answer-check · code-check)
  py/_hook_output.py 모델에게 알리는 JSON 출력
crates/kl-gate/      Rust 훅 본체. 모든 게이트를 `match` 하나로 처리
                     판단 로직은 순수 함수로 빼서 `cargo test` 로 고정
bin/                 빌드된 실행파일 — CI 가 채운다. 손으로 넣지 않는다
version-files.txt    plugin.json 말고도 버전이 적힌 파일 목록. plugin-release 가 같이 올린다
scripts/
  bench-hook-startup.py  Rust 훅 vs Python 훅 시작 시간 측정
results/             측정 결과. 파일명에 환경·n·날짜를 넣어 덮어쓰지 않는다
tests/selftest*.sh   셀프테스트. CI 가 이 패턴 전부를 돌린다
  selftest.sh                  run.sh 가 실행파일·인터프리터를 제대로 고르는지
  selftest-readme.sh           README 의 개수·스킬·게이트가 실제 저장소와 맞는지
  selftest-banner.sh           배너가 말하는 게이트 개수가 hooks.json 과 맞는지
  selftest-new-topic.sh        위키 주제 생성 스크립트가 덮어쓰지 않는지
  selftest-wiki-scripts.sh     인덱스·로그·lint 스크립트가 제대로 동작하는지
  selftest-wiki-sync.sh        쉘로 고친 페이지(= 훅이 못 본 변경)를 세션 끝에 잡는지
  selftest-wiki-touch.sh       같은 변경을 Bash 직후에 바로 잡는지 (바이너리 필요)
  selftest-wiki-recall.sh      맞는 페이지가 먼저 나오고, 무관한 메시지에는 훅이 조용한지
  selftest-graph.sh            그래프 DB 집계가 맞는지 + 뷰어가 실제로 그려지는지
                               (크롬이 있으면 헤드리스로 띄워서 노드가 그려졌는지 센다)
  selftest-prose.sh            생략 많은 글은 걸리고 잘 쓴 글은 조용한지 (검사별로 한 줄씩)
  selftest-readable-code.sh    나쁜 이름·빠진 설명문을 잡고, 잘 쓴 코드는 조용한지
  selftest-code-check.sh       그 검사를 훅으로 걸었을 때 조용해야 할 경우에 조용한지
  selftest-answer-check.sh     되물었을 때만 막고, 파일을 고친 턴은 작업 보고 6단계를 요구하고,
                               한 번 막은 뒤에는 안 막는지(무한 반복 방지)
  selftest-pipeline-debug.sh   세 단계 중 둘째에서 생긴 빈 칸이 숫자로 드러나는지
  selftest-planner.sh          잘 쓴 기획서는 깨끗하고, 목표 연결이 끊긴 기획서·계획 밖 일은 걸리는지
  selftest-hook-replay.sh      시점을 맞게 자르고(stop·prompt), 기계 글은 시점으로 안 세는지
  selftest-plugin-release.sh   CI 가 실패하면 설치 명령을 한 번도 안 부르는지, 굳은 바이너리를 잡는지
  release_paths_check.py       (위 테스트가 부름) 워크플로 모양·경로 규칙·파일 이름별 CI 판정
  selftest-research-to-wiki.sh 잘 쓴 조사 페이지는 조용하고, 빠진 표시는 이름대로 걸리는지
.github/workflows/build.yml   5종 빌드 → bin/ 에 자동 커밋
```

</details>

## 핵심 개념

<details>
<summary><strong>스킬 · 훅 게이트 · 위키가 각각 무엇인지</strong></summary>

### 스킬

필요할 때만 읽히는 작업 설명서다. 앞머리의 `description` 이 "언제 읽을지"를 정한다. 대화가 그 설명과
맞으면 Claude 가 읽는다.

```markdown
---
name: pipeline-debug
description: When code fails or gives a wrong result, trace the error back along the pipeline ...
---

# Pipeline Debug

에러는 원인보다 아래쪽에서 보인다. ...
```

판정 기준이 되는 목록(허용 약어, 근거 수준 이름 등)은 스킬의 `data/` 에 따로 둔다. 코드에 박지 않는다.

### 훅 게이트

정해진 사건(세션 시작, 파일 쓰기, Bash 실행, 답 끝, 메시지 받기)마다 도는 작은 프로그램이다.
`hooks/hooks.json` 에 사건과 명령을 적고, 명령은 모두 런처 `run.sh <게이트>` 를 거친다.

```json
{
  "type": "command",
  "command": "sh \"${CLAUDE_PLUGIN_ROOT}/hooks/run.sh\" answer-check",
  "timeout": 30,
  "id": "stop:answer-check"
}
```

모델에게 알리려면 JSON 한 덩어리를 찍는다. 그냥 찍은 글은 대부분 모델에게 가지 않는다(아래 [개발](#개발) 참고).

### 위키

`~/llm-wiki-docs/<주제>/wiki/` 아래, 한 주제 한 페이지로 쌓이는 지식이다. 페이지마다 `index.md` 에
한 줄, 바꿀 때마다 `log.md` 에 한 줄을 남긴다. `wiki-recall` 이 매 메시지마다 여기서 찾아 붙이고,
`graph-doc-memory` 가 페이지 사이의 링크를 그래프로 그린다.

</details>

## 왜 kl-skills 인가

| 없을 때 | 있을 때 |
| --- | --- |
| 알게 된 것이 대화와 함께 사라진다 | 위키에 한 주제 한 페이지로 남고, 다음 질문 때 자동으로 찾아 붙는다 |
| "쉽게 써 줘"는 대화가 길어지면 잊히는 지시다 | 답이 끝날 때마다 훅이 읽고, 뜻 없는 용어·긴 답·되물음이면 한 번 막는다 |
| 코드를 고치고 "됐습니다"로 끝난다 | 작업 보고 6단계(결과·요약·변경·검증·제약·후속)가 없으면 막는다 |
| 배포 순서를 건너뛰어 옛 바이너리가 굳는다 | CI 통과를 확인하기 전에는 설치 명령을 부르지 않는다 |
| 훅을 고쳐도 실제 대화에서 어떨지 모른다 | 실제 대화 기록에 다시 돌려 몇 번 잘못 떴는지 센다 |
| 쥐 실험이 사람 증거처럼 적힌다 | 출처마다 근거 수준·읽은 수준을 적게 하고, 빠지면 검사가 잡는다 |

### 스킬과 훅이 나눠 맡는 일

| 무엇 | 하는 일 | 언제 쓰이나 |
| --- | --- | --- |
| 스킬 | 방법을 알려 준다 — 위키 규약, 답변 규칙, 기획 절차 | 대화가 설명과 맞을 때만 읽힌다 |
| 훅 게이트 | 지켰는지 본다 — 답 검사, 목차 확인, 이름 검사 | 정해진 사건마다 돈다. 모델의 대화 맥락 밖에서 돈다 |
| 위키 | 알게 된 것을 쌓는다 | 관련 페이지만 골라 붙는다 |
| 데이터 파일 | 판정 기준을 담는다 — 허용 약어, 되묻는 말투, 근거 수준 이름 | 검사가 돌 때 읽는다. 고치려면 코드 대신 이 파일을 고친다 |

<details>
<summary><strong>왜 <code>Stop</code> 게이트가 따로 있나</strong></summary>

`PostToolUse` 는 `Write`·`Edit`·`MultiEdit` 에만 걸린다. 그런데 모델은 **파일을 Bash 로도
쓴다** — heredoc(= 셸에서 여러 줄 텍스트를 파일로 쏟아 넣는 문법), `sed`, 짧은 python 스크립트.
그러면 위의 게이트들이 전부 조용히 넘어가고, 그래프는 위키보다 뒤처진 채로 남는다. 2026-11-11 에
실제로 그랬다: 어떤 세션이 조사 결과를 페이지·목차·기록에 다 반영했는데, 전부 Bash 로 써서
아무 게이트도 돌지 않았다.

발동 조건에 `Bash` 를 넣는 것이 당연해 보이지만 비싸다. Bash 는 가장 자주 쓰는 도구이고, 사건
내용에 담겨 오는 것은 경로가 아니라 명령문이며, 그 안의 쉘 변수는 풀 수 없다. 그래서 `wiki-sync` 는
**세션당 한 번** 돌면서 파일시스템에 묻는다 — `graph.json` 보다 새 페이지가 바뀐 페이지다. 어떻게
썼는지는 묻지 않는다. `graph.json` 이 기준점을 겸한다. 다시 만들면 그 파일의 수정 시각이 앞으로
가므로, 다음 세션은 알아서 맞는 지점과 비교한다.

`wiki-index-check` 가 Rust 인 이유: `PostToolUse` 는 파일을 쓸 때마다 돈다. 위키 밖 경로면 JSON 에서
경로 하나 읽고 바로 끝낸다. 반대로 `wiki-graph` 와 `prose-check` 는 같은 사건에 걸리지만 Python 이다.
**두 훅이 실제로 하는 일이 둘 다 Python 이라서다** — 그래프를 만드는 빌더와 글을 검사하는 스크립트.
게이트만 Rust 로 옮기면 Python 프로세스가 사라지지 않고 하나가 더 붙는다. 위키 밖 경로면 문자열
몇 개만 비교하고 끝나므로, 드는 비용은 Python 이 한 번 뜨는 약 32 ms 이고 그것도 파일을 쓸 때만 든다.

</details>

## 지원 환경

| 컴퓨터 | 실행파일 |
| --- | --- |
| 맥 (M1 이후) | `bin/kl-gate-aarch64-apple-darwin` |
| 맥 (인텔) | `bin/kl-gate-x86_64-apple-darwin` |
| 리눅스 x86_64 · WSL(= 윈도우 안에서 리눅스를 돌리는 환경) | `bin/kl-gate-x86_64-unknown-linux-musl` |
| 리눅스 ARM(= 휴대폰·라즈베리파이 같은 저전력 칩) | `bin/kl-gate-aarch64-unknown-linux-musl` |
| 윈도우 | `bin/kl-gate-x86_64-pc-windows-msvc.exe` |

리눅스용은 `musl`(= 필요한 부품을 실행파일 안에 다 넣는 방식)로 만들어서, 오래된 리눅스에서도
"라이브러리 버전이 안 맞는다"는 에러가 나지 않는다. ARM(= 휴대폰 계열의 저전력 칩) 윈도우 컴퓨터는
x86_64 실행파일을 에뮬레이션으로 돌리므로 따로 만들지 않았다. **목록에 없는 환경**(FreeBSD, RISC-V 등)에서는
훅이 조용히 통과한다. 세션이 깨지는 것보다 규칙이 안 걸리는 게 낫다는 판단이다.

## 요구 사항

| 무엇 | 왜 필요한가 | 없으면 |
| --- | --- | --- |
| Claude Code | 플러그인을 설치하고 훅을 돌린다 | 설치 자체가 안 된다 |
| `python3` | 게이트 대부분과 모든 스킬 스크립트가 Python 이다. 표준 라이브러리만 쓴다 — 따로 설치할 패키지가 없다 | 그 훅들이 조용히 통과한다 |
| `git` | `plugin-release` 가 커밋·푸시 상태를 보고, 계획 이탈 검사가 커밋을 읽는다 | 그 둘만 안 된다 |
| `gh` (GitHub 명령줄 도구) | `plugin-release ship` 이 CI 결과를 기다린다 | `ship` 만 안 된다. 나머지는 상관없다 |
| 크롬 (선택) | `selftest-graph.sh` 가 그래프 뷰어를 실제로 띄워 본다 | 그 검사 하나만 건너뛴다 |

## 보안

- 훅과 스킬 스크립트는 네트워크를 쓰지 않는다. 예외는 `plugin-release` 하나로, `gh`·`claude` 명령을 불러
  CI 결과를 보고 플러그인을 갱신한다
- 위키·그래프·계획서는 모두 사용자 컴퓨터 안에 남는다. 밖으로 보내지 않는다
- 훅은 판단이 안 서면 0으로 끝난다(= 통과). 훅이 터지면 그 사건이 걸린 모든 세션이 깨지기 때문이다
- 막는 훅은 `answer-check` 하나이고, 한 턴에 한 번만 막는다 — 무한 반복으로 세션이 멈추지 않는다

## 개발

<details>
<summary><strong>훅을 어떤 언어로 쓸까 — Rust 와 Python</strong></summary>

Rust 만 쓰지 않는다. 갈리는 지점은 **설치받는 컴퓨터에 뭐가 있어야 하는가**와 **그 훅이 얼마나 자주
도는가** 두 가지다.

| | Rust | Python |
| --- | --- | --- |
| 설치받는 컴퓨터에 필요한 것 | 없음 (실행파일이 리포에 있음) | `python3` |
| 윈도우 | 됨 | 대개 안 깔려 있음 |
| 고치고 확인 | CI 빌드 약 1분 | 즉시 |
| 훅 한 번 시작 시간 | 4.5 ms | 32.0 ms |

시작 시간은 이 맥에서 실제로 쟀다 — 중앙값, 각 30회. 재는 방법과 결과는
`scripts/bench-hook-startup.py` 와 `results/hook-startup_macos-arm64_n30_20261111.txt`. 둘 다 프로세스를
띄우는 비용을 똑같이 포함하므로, **의미 있는 건 차이인 27.5 ms** 다. 다른 컴퓨터·다른 Python 버전에서는
달라지니, 궁금하면 그 컴퓨터에서 다시 돌려보면 된다.

27.5 ms 가 문제가 되는 이유: `PreToolUse` 는 **도구를 쓸 때마다** 돈다. Bash 를 100번 쓰면 100번
돌아서 약 2.8초가 쌓인다. 반대로 `SessionStart`·`Stop` 은 세션당 한 번이라 27.5 ms 는 체감되지 않는다.

- **Python** — 세션당 몇 번만 도는 훅(`SessionStart`, `Stop`, `SubagentStop`), 텍스트·JSON 을 많이
  다루는 규칙, 일단 만들어보고 싶을 때
- **Rust** — 모든 도구 호출마다 도는 훅(`PreToolUse`, `PostToolUse`), 윈도우에서 반드시 돌아야 하는 규칙

Python 으로 시작해서 느리면 Rust 로 옮기는 게 기본 경로다. `hooks.json` 은 안 고쳐도 된다 —
`.py` 를 지우면 그때부터 Rust 쪽이 처리한다.

</details>

<details>
<summary><strong>훅 추가하기 — Python · Rust</strong></summary>

**Python 훅**

1. `hooks/py/<게이트이름>.py` 를 만든다. 게이트 이름이 `argv[1]` 로 들어오고, 사건 내용(JSON)이 표준입력으로 들어온다
2. `hooks/hooks.json` 에 그 사건을 등록한다 — 명령은 Rust 와 **똑같이** `run.sh <게이트이름>`
3. 푸시하면 끝. 빌드 없음

**Rust 훅**

1. `crates/kl-gate/src/main.rs` 의 `match event` 에 분기를 추가한다
2. `hooks/hooks.json` 에 그 사건을 등록한다 (`PostToolUse`, `Stop` 등)
3. `crates/**` 를 푸시하면 CI 가 5종을 다시 빌드해서 `bin/` 에 커밋한다

</details>

<details>
<summary><strong>두 언어가 공유하는 규약 — 출력이 모델에게 가는 방법</strong></summary>

- 게이트 이름은 `argv[1]`, 사건 내용(JSON)은 표준입력
- 종료 코드: `0` = 통과, `2` = 차단(stderr 가 모델에 보임)
- **그냥 찍은 출력(stdout)은 대부분 모델에게 가지 않는다.** `SessionStart` 는 가지만, `PostToolUse` 와
  `Stop` 의 stdout 은 디버그 기록에만 남는다. 모델에게 알리려면 JSON 한 덩어리를 찍는다:
  `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "..."}}`.
  Python 은 `hooks/py/_hook_output.py` 의 `tell_model`, Rust 는 `model_note` 를 쓴다.
  막아야 할 때(Stop)는 `{"decision": "block", "reason": "..."}` 이다
- 이 규약을 몰라서 2026-11-11 까지 게이트 넷의 지적이 **기록에만 쌓이고 아무도 못 읽었다.**
  예전 판의 이 README 가 "stdout 은 모델에 전달됨" 이라고 적고 있었다
- **판단이 안 서면 반드시 0.** 훅이 터지면 그 사건이 걸린 모든 세션이 깨진다. 런처(`run.sh`/`run.ps1`)도
  같은 원칙이라, 실행할 게 없으면 조용히 0으로 빠진다

</details>

<details>
<summary><strong>로컬 빌드와 테스트</strong></summary>

이 리포는 Rust 없이도 **쓸** 수 있다. Rust 훅을 고치려면 빌드가 필요하다:

```sh
cargo test                                        # Rust 훅 판단 로직 단위 테스트
cargo build --release                             # 현재 컴퓨터용
for t in tests/selftest*.sh; do sh "$t"; done     # 셀프테스트 전부
claude plugin validate .                          # 플러그인·스킬 형식 검사
```

5종 전부는 로컬에서 만들 수 없다(윈도우·맥 SDK 라이선스 문제). CI 가 한다.
CI 는 `crates/`·`hooks/`·`Cargo.toml`·워크플로 파일이 바뀐 커밋에만 돈다. 스킬·문서만 바꿨다면
셀프테스트를 직접 돌린다. 훅을 고쳤다면 테스트만으로 끝내지 말고 `hook-replay` 로 실제 대화 기록에
한 번 돌려 본다 — 테스트는 만든 사람이 상상한 대화만 담고 있다.

</details>

## 라이선스

MIT
