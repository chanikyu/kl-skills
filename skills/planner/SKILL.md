---
name: planner
description: Plan a project the way the field it belongs to plans - business strategy, service and web, UI/UX, product, content, software, advertising, production and quality each start from different questions and end in different documents. Fix the frame first (which field, which horizon, which level), then run the work in order - find the problem or opportunity through research, set goals and targets, test feasibility and competitiveness, define features and the concept, then write requirements and functional specs, design the information structure and flows, draw wireframes and screen specs, and set the schedule with the related teams, played by subagents. Long-, mid- and short-term plans cascade - every mid-term goal serves a long-term one and every short-term task serves a mid-term one, numbered so an orphan task shows up mechanically. Use this whenever asked to plan, scope, or write a plan, roadmap, proposal, PRD, requirements, functional spec, IA, flowchart, wireframe or schedule. Triggers - plan, planning, roadmap, strategy, proposal, PRD, requirements, spec, IA, information architecture, flowchart, wireframe, storyboard, schedule, milestone, 기획, 기획서, 계획, 로드맵, 전략, 제안서, 요구사항, 기능명세, 정보구조, 플로우차트, 와이어프레임, 화면설계, 일정, 마일스톤, 단기 중기 장기.
---

# Planner

기획이 틀어지는 가장 흔한 경로는 **분야에 맞지 않는 틀로 시작하는 것**이다. 광고 캠페인을
소프트웨어 요구사항처럼 쓰면 매체 계획이 빠지고, 생산 계획을 서비스 기획서처럼 쓰면 공정과
불량률이 빠진다. 그래서 무엇을 쓰기 전에 틀부터 정한다.

## 1부 — 틀 정하기 (쓰기 전에)

### ① 분야

프로젝트가 어느 분야인지 먼저 판별한다. 분야마다 **출발하는 질문과 끝나는 문서가 다르다.**
여덟 분야의 초점 질문, 핵심 산출물, 쓰는 분석 틀, 흔한 함정은 `references/domains.md` 에 있다.
해당 분야의 절 하나만 읽는다.

경영·전략 / 서비스·웹 / UI·UX(= 화면과 사용 경험) / 상품 / 콘텐츠 / 소프트웨어 / 광고 / 생산·품질

둘 이상에 걸치면(예: 웹 서비스 + 광고 캠페인) **주 분야 하나**를 정하고, 나머지는 그 분야의
산출물에서 빠지는 것만 덧붙인다. 두 틀을 섞어 쓰면 어느 쪽도 끝나지 않는다.

### ② 기간 — 위에서 아래로

장기를 먼저 정하고, 중기는 장기에 맞추고, 단기는 중기에 맞춘다. **거꾸로 쌓지 않는다.**
단기 할 일부터 모으면 그럴듯한 목록은 생기지만 어디로 가는지가 없다.

| 기간 | 경영·사업 규모 | 프로젝트 규모 | 답하는 질문 |
|---|---|---|---|
| 장기 | 3~5년 | 프로젝트 전체 (6~12개월) | 어디에 도착하려는가 |
| 중기 | 1~3년 | 분기·마일스톤 | 그러려면 어떤 단계를 거치는가 |
| 단기 | 1년 이하 | 2주~1개월 | 지금 무엇을 하는가 |

기간은 절대값이 아니다. 프로젝트 규모에 맞춰 위 두 열 중 하나를 고른다.

### ③ 수준 — 기간과 짝을 이룬다

| 수준 | 짝이 되는 기간 | 정하는 것 | 목표 번호 |
|---|---|---|---|
| 전략적 기획 | 장기 | 무엇을, 왜 — 방향과 자원 배분 | `L1`, `L2` … |
| 전술적 기획 | 중기 | 어떻게 — 부문별 실행 방법 | `M1.1`, `M1.2` … |
| 운영적 기획 | 단기 | 누가, 언제 — 작업과 일정 | `S1.1.1` … |

**번호가 부모를 말한다.** `M1.2` 는 `L1` 아래, `S1.2.3` 은 `M1.2` 아래다. 부모 번호가 없는
목표는 위 기간과 연결이 끊긴 것이다. `scripts/check_plan.py` 가 그것을 찾는다.

## 2부 — 진행

### 1. 방향성 정의 및 핵심 도출

1. **문제점·기회 발견 (리서치)** — 누가 어떤 상황에서 무엇 때문에 곤란한가. 근거는 출처를
   붙인다. 추측은 추측이라고 적는다
2. **목표·타깃 설정** — 여기서 `L` → `M` → `S` 목표를 쌓는다. 목표마다 **잴 수 있는 기준**을
   붙인다(숫자, 기한). 기준이 없는 목표는 바람이다
3. **타당성·경쟁력 검토** — 할 수 있는가(자원·기술·일정), 할 가치가 있는가(시장·비용),
   남보다 나은가(경쟁 대안과 비교). **안 하는 것이 답일 수 있다** — 그러면 그렇게 쓴다
4. **기능 정의·컨셉 도출** — 목표를 이루는 데 필요한 것만 기능으로 남긴다. 기능마다 어느 목표
   번호를 위한 것인지 적는다. 번호가 없는 기능은 빼거나, 빠진 목표를 찾는다

### 2. 문서화 및 설계

1. **요구사항 정의서·기능명세서** — 무엇을 만족해야 하는가(요구사항), 각 기능이 정확히 무엇을
   하는가(명세). 요구사항마다 확인할 방법을 같이 쓴다
2. **정보 구조·플로우차트** — 무엇이 어디에 있는가(정보 구조), 사용자나 일이 어떤 순서로
   흐르는가(플로우)
3. **와이어프레임·화면 설계서** — 화면이 있는 분야만. 생산·경영 분야는 이 자리에 공정
   흐름도나 조직·프로세스 도식을 둔다
4. **일정 수립·유관부서 조율** — 단기 목표가 여기서 "누가, 언제"가 된다. 유관부서는
   서브에이전트가 맡는다 (아래)

산출물의 모양은 `assets/plan-template.md` 를 쓴다. 다 쓰면 `scripts/check_plan.py` 로
목표 연결과 빠진 단계를 확인한다.

## 유관부서 조율 — 서브에이전트

2부 4단계에서 계획을 **해당 부서 관점**으로 검토받는다. 각 부서에게는 계획 전체가 아니라
**그 부서가 맡을 부분**과 아래 네 질문만 준다.

> 이 부분을 할 수 있는가 · 무엇이 걸리는가 · 무엇이 더 필요한가 · 일정에 어떤 영향이 있는가

| 부서 | 맡기는 에이전트 | 주로 부르는 분야 |
|---|---|---|
| 개발 | `architect` 또는 `planner`(에이전트) | 소프트웨어, 서비스·웹 |
| 디자인·접근성 | `a11y-architect` | UI·UX, 서비스·웹 |
| 보안 | `security-reviewer` | 개인정보·결제가 있는 모든 분야 |
| 데이터 | `database-reviewer` | 데이터를 저장하는 모든 분야 |
| 마케팅·검색 노출 | `seo-specialist` | 광고, 콘텐츠, 서비스·웹 |
| 재무·생산·품질·법무 | `general-purpose` 에 역할을 주어 | 경영·전략, 상품, 생산·품질 |

부르는 원칙 세 가지다.

1. **필요한 부서만**, 보통 두세 곳. 다섯을 넘기면 조율보다 비용이 커진다
2. **한 번에 나란히** 보낸다. 앞 부서의 답을 기다릴 이유가 없다
3. **돌아온 답을 그대로 옮기지 않는다.** 부서끼리 부딪히는 지점을 찾아 정리하고, 그 결과로
   일정을 고친다. 부딪힘을 정리하는 것이 기획자의 일이다

## 하지 말 것

- 분야를 정하지 않고 일반 틀로 쓰기
- 단기 할 일부터 모아 장기를 끼워 맞추기
- 부모 번호가 없는 중기·단기 목표
- 잴 기준이 없는 목표
- 어느 목표를 위한 것인지 말하지 못하는 기능
- 타당성 검토에서 "안 한다"는 답을 지우기
- 유관부서 의견을 정리 없이 이어 붙이기

## 다른 규칙과의 경계

| 무엇을 정하나 | 어디 |
|---|---|
| 사업·서비스·제품의 기획 전반 | 이 스킬 |
| 코드를 어떤 순서로 어떻게 바꿀지 | `planner` 에이전트 (이 스킬의 개발 부서 역할로도 쓴다) |
| 기획 문서를 어디에 둘지 (프로젝트 문서인가 위키인가) | `llm-wiki-docs` 스킬의 경계 절 |
| 기획서의 문장 | `natural-answering` 스킬 |
