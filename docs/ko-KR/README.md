<div align="center">

<img src="../../assets/hero.png" alt="kl-skills — Claude Code 용 스킬과 훅 게이트를 한 번에 설치한다. 설치 명령 두 줄과, 다시 시작하면 뜨는 배너." width="100%" />

<br />

<img src="https://img.shields.io/badge/Claude%20Code-plugin-D97757?logo=anthropic&logoColor=white" alt="Claude Code plugin" />
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license" />
<img src="https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-57606A" alt="macOS, Linux, Windows" />

[English](../../README.md) · **한국어** · [日本語](../ja-JP/README.md) · [简体中文](../zh-CN/README.md) · [Español](../es/README.md)

[설치](#설치) · [시작하기](#시작하기) · [들어 있는 것](#들어-있는-것) · [새 소식](#새-소식)

</div>

<br />

## 한눈에

Claude Code 는 대화가 끝나면 알게 된 것을 잊고, 긴 대화에서는 "쉽게 써 줘" 같은 규칙에서 멀어진다.

`kl-skills` 는 Claude 가 알게 된 것을 위키에 남겨 다음 대화에서 다시 꺼내 쓴다. 지킬 규칙은 훅에 걸어 답할 때마다 검사한다.

<img src="../../assets/turn-flow.png" alt="한 턴: 세션 시작, 메시지 받음, 파일 쓰기, Bash 실행, 답 끝. 순간마다 그때의 훅 게이트가 돈다." width="100%" />

| 들어 있는 것 | 개수 | 하는 일 |
| --- | --: | --- |
| 스킬 | 9개 | 위키, 쉬운 답변, 코드 규칙, 기획, 디버깅, 문헌 조사 |
| 훅 게이트 | 9개 | 답 검사, 위키 관리, 글·코드 검사, 계획 이탈 |

<br />

## 설치

```
/plugin marketplace add chanikyu/kl-skills
/plugin install kl-skills@kl-skills
```

세션을 다시 시작하면 첫 줄에 이것이 뜬다.

```
KL-SKILLS GATES v<버전> — loaded, 9 rules enforced
```

> [!IMPORTANT]
> 게이트 대부분이 Python 이다. `python3` 가 없으면 그 게이트들은 조용히 건너뛴다.

**업데이트** — `claude plugin marketplace update kl-skills` → `claude plugin update kl-skills@kl-skills` → 세션 다시 시작.<br />
**지우기** — `claude plugin uninstall kl-skills@kl-skills`. 위키(`~/llm-wiki-docs/`)는 남는다.

<br />

## 시작하기

하려는 일에서 시작한다. 스킬은 대화가 설명과 맞으면 저절로 읽히고, 이름을 말해도 된다.

| 하려는 일 | 이렇게 말한다 | 스킬 |
| --- | --- | --- |
| 알게 된 것 남기기 | "위키에 정리해줘" | `llm-wiki-docs` |
| 위키에서 찾아 쓰기 | 말할 것 없음 — 매 메시지마다 위키와 맞춰 본다 | `wiki-recall` |
| 위키 한눈에 보기 | "위키 그래프 보여줘" | `graph-doc-memory` |
| 문헌 조사 | "○○가 원인인지 리서치해줘" | `research-to-wiki` |
| 기획 | "planner 로 기획해줘" | `planner` |
| 에러 원인 찾기 | "이 에러 원인 찾아줘" | `pipeline-debug` |
| 코드 쓰기 | 말할 것 없음 — 이름·주석·값 규칙이 함께 적용된다 | `readable-code` · `no-hardcoding` |

게이트가 답을 막으면 대화에 `Stop hook feedback:` 과 이유가 뜨고, Claude 가 답을 고쳐 쓴다. 막는 게이트는 `answer-check` 하나뿐이고, 한 턴에 한 번만 막는다.

<br />

## 들어 있는 것

<img src="../../assets/parts.png" alt="메시지가 Claude Code 로 가고, Claude Code 는 스킬을 읽고, 훅 게이트의 검사를 받고, 알게 된 것을 위키에 남긴다." width="100%" />

### 스킬

| 스킬 | 하는 일 |
| --- | --- |
| `llm-wiki-docs` | 알게 된 것을 한 주제 한 페이지로 위키에 모은다 |
| `wiki-recall` | 관련 위키 페이지를 찾아 답에 쓴다 |
| `graph-doc-memory` | 위키 전체를 그래프로 그려 브라우저에 띄운다 |
| `research-to-wiki` | 출처마다 연구 종류와 읽은 수준을 적어 조사를 남긴다 |
| `natural-answering` | 용어·비교 기준·결론까지의 중간 단계를 생략하지 않게 쓴다 |
| `readable-code` | 이름은 담긴 것대로, 주석에는 왜 그렇게 했는지 |
| `no-hardcoding` | 목록·경로·임계값을 코드에 박지 않는다 |
| `pipeline-debug` | 에러가 난 줄이 아니라 처음 틀어진 단계를 찾는다 |
| `planner` | 분야·기간에 맞춰 기획하고, 계획에서 벗어난 일을 알린다 |

### 훅 게이트

| 언제 | 게이트 | 하는 일 |
| --- | --- | --- |
| 세션 시작 | `session-start` | 배너를 띄운다 |
| 메시지 받음 | `wiki-recall` | 관련 위키 페이지를 붙인다 |
| 파일 쓰기 | `wiki-index-check` | 위키 목차에 없는 페이지를 알린다 |
| 파일 쓰기 | `wiki-graph` | 위키 그래프를 다시 그린다 |
| 파일 쓰기 | `prose-check` | 위키 글에서 읽기 어려운 자리를 알린다 |
| 파일 쓰기 | `code-check` | 모호한 파이썬 이름과 빠진 설명문을 알린다 |
| 파일 쓰기 | `plan-drift` | 계획서의 틀과 이탈을 본다 |
| Bash 실행 | `after-bash` | 쉘로 고친 위키와 커밋을 알아챈다 |
| 답 끝 | `wiki-sync` | 어떻게 고쳤든 그래프를 최신으로 맞춘다 |
| 답 끝 | `answer-check` | 답을 검사하고, 필요하면 한 번 막는다 |

<br />

## 새 소식

0.17~0.20 은 2026-11-11, 0.21 은 2026-11-12 에 나왔다. 전체 기록은 `git log`.

- **0.21** — 관리자용 스킬(`plugin-release`, `hook-replay`)을 플러그인에서 뺐다. README 5개 언어
- **0.20** — 파일을 고친 턴은 작업 보고 6단계로 끝내야 한다
- **0.19** — `hook-replay`, `plugin-release`, `research-to-wiki`
- **0.18** — 정말로 다시 물었을 때만 막는다. 계획 이탈 알림과 위키 자동 검색
- **0.17** — `planner`

<br />

## 요구 사항

| 필요한 것 | 쓰는 곳 | 없으면 |
| --- | --- | --- |
| `python3` | 게이트 대부분, 모든 스킬 스크립트 (표준 라이브러리만) | 그 게이트들이 조용히 건너뛴다 |
| `git` | 계획 이탈 검사 | 그 검사를 건너뛴다 |

미리 빌드한 게이트는 맥(애플 칩·인텔), 리눅스(x86_64·ARM, WSL 포함), 윈도우(x86_64)용이 들어 있다. 그 밖의 환경에서는 게이트가 조용히 통과한다.

<br />

## 보안

- 게이트와 스킬 스크립트는 네트워크를 쓰지 않는다.
- 위키·그래프·계획서는 사용자 컴퓨터 밖으로 나가지 않는다.
- 게이트는 판단이 안 서면 통과시킨다.

<br />

## 개발

배포, 실제 대화로 훅 확인하기, 훅 출력 규약, 파일 구조: [docs/DEVELOPMENT.md](../DEVELOPMENT.md) (영어).

## 라이선스

MIT
