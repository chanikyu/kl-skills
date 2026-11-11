---
name: natural-answering
description: Write answers, reports, and documents that a reader can follow on the first pass, by refusing to omit the links in the explanation. Use this whenever you write anything a person will read - a report on what you did or found, an analysis result, a plan, a document, a README, an architecture or API document, a commit message, an answer to a question, even a one-line reply. It governs HOW the writing is done, which is the part the reporting rules do not cover: every term glossed where it first appears, every number tied to what it should be compared with, the step between a number and the conclusion spelled out, the subject of the sentence present, units translated into everyday words, and a lead-in sentence before every table. It also fixes the order a work report is written in (result, summary, changes, verification, open problems, next steps) and the skeleton of a document that is not a wiki page (README, architecture, API reference, developer guide, analysis pipeline, troubleshooting, research report). Also use it to repair text that already reads badly, when asked "무슨 말인지 모르겠다 / 이해가 안 된다 / 다시 설명해줘 / 풀어서 써줘 / 말이 이상하다 / 너무 압축됐다". Triggers - report, write-up, explain, summary, document, README, architecture, API docs, answer, 보고, 작업 보고, 변경사항, 검증 결과, 설명, 리포트, 문서 작성, 문서 구조, 결과 정리, 풀어 쓰기, 쉽게 설명, 이해 안 됨, 말이 이상함, 생략, 압축.
---

# Natural Answering

## 왜 이 스킬이 있나

실제로 일어난 일이다. 20분짜리 분석을 끝내고 결과를 보고했더니 이런 답이 돌아왔다:

> 그래서 위의 결과가 뭔데???? 말을 너무 생략한 부분이 많아서 이해하기가 어려워

보고에 틀린 내용은 없었다. 숫자도 맞았고 표도 정확했다. 문제는 **읽는 사람이 알아야 하는
중간 단계를 전부 빼고 결론만 늘어놓은 것**이었다. 같은 내용을 생략 없이 다시 쓰자 바로 이해됐다.

빠진 것은 문법이 아니라 **설명의 사슬**이었다. 이 스킬은 그 사슬을 빼먹지 않게 하는 규칙이다.

## 생략하면 안 되는 여섯 가지

전부 위 사건에서 실제로 빠졌던 것이다. 왼쪽이 처음 쓴 것, 오른쪽이 다시 쓴 것이다.

### 1. 용어의 뜻 — 처음 나오는 자리에서

```
나쁨: cross-mapping 위험은 낮습니다. 서로 다른 종 locus 294쌍 중 최장 완전일치가 34bp입니다.
좋음: 한 종의 DNA 조각을 다른 종의 것으로 착각할 위험(= cross-mapping)은 낮습니다.
      유전자 자리(= locus) 294쌍을 비교했더니, 글자가 하나도 안 틀리고 이어지는
      가장 긴 구간이 34글자였습니다.
```

`용어(= 쉬운 뜻 한 문장, 가능하면 비유)` 형태로 그 자리에서 푼다. 뒤에 모아서 설명하지 않는다 —
읽는 사람은 그 문장에서 이미 멈춘다.

### 2. 숫자에서 결론으로 가는 중간 단계

이것이 가장 많이 빠지고, 빠지면 가장 치명적이다. 숫자와 결론만 붙여 놓으면 읽는 사람은
**왜 그 숫자가 그 결론이 되는지** 알 수 없다.

```
나쁨: 최장 완전일치가 34bp입니다. 따라서 cross-mapping 위험은 낮습니다.
좋음: 기계는 DNA를 100글자씩 토막 내어 읽습니다. 그 토막이 엉뚱한 종에 붙으려면 100글자가
      다 맞아야 하는데, 두 종이 똑같은 구간은 최대 34글자뿐입니다. 나머지 66글자가 다르면
      프로그램이 버립니다. 그래서 위험이 낮습니다.
```

**검사법**: 결론 문장 앞에 "왜?"를 넣어 읽어 본다. 답이 글에 없으면 그 자리가 빈 것이다.

### 3. 비교 기준 — 그 숫자가 좋은 건지 나쁜 건지

```
나쁨: 완전일치 34bp.
좋음: 완전일치 34글자 — 토막 하나가 100글자이므로 그보다 훨씬 짧다(= 안전하다).
```

숫자 하나를 쓸 때마다 "무엇과 견주어 그런가"를 같은 문장이나 바로 다음 문장에 붙인다.

### 4. 문제 설정 — 무엇을 걱정해서 이걸 했는지

결과부터 시작하면 읽는 사람은 **그게 왜 중요한지 모르는 상태로** 숫자를 받는다.
한 문단으로 "이런 사고가 가능해서 그게 얼마나 일어나는지 재 봤다"를 먼저 그린다.

### 5. 주어 — 무엇이 그렇게 되는가

```
나쁨: 위키 밖 경로면 문자열 비교 몇 번으로 끝납니다.
좋음: 위키 밖 경로면 훅이 문자열 몇 개만 비교하고 바로 끝냅니다.

나쁨: 그마저 파일을 쓸 때만이다.
좋음: 그 비용도 파일을 쓸 때만 든다.
```

### 6. 단위를 일상어로

`bp → 글자`, `read → 토막`, `294쌍 → 294번의 비교`. 전문 단위를 그대로 두면 숫자의 크기가
읽는 사람에게 전달되지 않는다. 원래 단위가 필요하면 괄호로 같이 쓴다: `34글자(34bp)`.

## 문장을 어색하게 만드는 것

| 쓰지 말 것 | 대신 |
|---|---|
| 이중 수동 — "생성되어진다" | "생성된다", 더 좋게는 "만든다" |
| 연결어미로 끝나는 문장 — "끝나므로." | 주절을 붙인다: "끝나므로 비용이 거의 없다." |
| 번역투 수동 — "훅에 의해 갱신된다" | 행위자를 주어로: "훅이 갱신한다" |
| 불필요한 사동 — "실행시킨다" | "실행한다" |
| 명사+하다로 늘리기 — "검사를 수행한다" | "검사한다" |
| 문장을 가리키는 말로 시작 — "이는 느리다" | 가리키는 것을 그 자리에 쓴다: "이 훅은 느리다" |
| 공문서투 — "해당 파일" | "그 파일" |

## 글의 뼈대 (보고·분석 결과)

위 사건에서 통했던 순서다. 결과가 여러 개면 **결과마다** 2·3번을 반복한다.

1. **무엇을 걱정했나** — 그림 하나를 그려 준다
2. **어떻게 쟀나** — 데이터가 무엇이고 한 줄이 무엇인지
3. **결과 N** — 숫자 → 그 숫자가 왜 그 뜻인지 → 그래서 무엇이 달라지는지
4. **내가 틀린 것** — 중간에 방법을 바꿨으면 왜 바꿨는지 숨기지 않는다
5. **아직 모르는 것** — 가장 큰 빈칸 하나. 결론의 범위를 좁혀서 말한다
   ("위험이 낮다"가 아니라 "비교한 유전자 7개 사이에서는 낮다")

표를 쓸 때는 **표 앞에 길잡이 한 줄**을 둔다 — "아래 표는 무엇과 무엇을 견준 것이다".
표만 던지면 읽는 사람이 어느 칸을 봐야 하는지 모른다.

## 작업 보고 — 코드를 고친 뒤

여섯 단계 순서로 쓴다: **작업 결과 → 작업 요약 → 변경사항 → 검증 결과 → 문제 및 제약 →
후속 조치.** 고친 과정과 자기평가를 늘어놓지 않는다. 읽는 사람이 알아야 할 것이 매번 같은
자리에 오게 한다. 세 가지만 지키면 나머지는 따라온다:

- "완료 / 부분 완료 / 실패"를 맨 앞 한 단어로 먼저 밝힌다
- 검증은 숫자로 쓴다 — "테스트 통과"가 아니라 "단위 테스트 12/12 통과"
- "문제 및 제약"을 비우지 않는다. 검증하지 않은 항목은 거의 항상 있다

전체 표와 예시는 `references/work-report.md` 를 읽는다.

## 문서 구조 — 위키가 아닌 문서

README·Architecture·API Reference 처럼 `~/llm-wiki-docs/` 밖에 만드는 문서는, 모든 문서에
같은 목차를 강제하지 않는다. **종류를 먼저 판별하고 그 종류의 뼈대를 쓴다.** 공통 10항목,
문서 종류별 구조, 쓸 때 지키는 일곱 가지는 `references/document-structure.md` 에 있다.

코드와 관련된 문서에서 가장 흔한 사고는 **없는 API나 돌려 보지 않은 명령어가 문서에 들어가는
것**이다. 명령어·경로·파라미터는 실제 구현과 대조한다(`source-of-truth.md`).
위키 페이지는 이 뼈대가 아니라 `llm-wiki-docs` 스킬의 규약을 따른다.

## 기계로 먼저 걸러내기

```bash
scripts/check_prose.py <파일...>        # 경고만
scripts/check_prose.py --all <파일...>  # 참고 등급까지
```

잡는 것:

- 뜻 없이 쓴 약어와 영문 용어
- 비교 기준 없는 숫자
- 90자 넘는 문장 (한글이 없는 문장은 180자)
- 연결어미로 끝나 주절이 빠진 문장
- 주어가 빠진 듯한 문장
- 비교 대상 없는 "더 ~", 개수 없는 "전부"
- 길잡이 문장 없이 바로 나오는 표
- 한 문단에 볼드 네 개 이상
- 이중 수동·번역투·공문서투
- 문서에 적혀 있지만 실제로 없는 파일 경로

판정 기준은 전부 `data/` 에 있다 — 패턴은 `patterns.tsv`, 설명 없이 써도 되는 약어와 영문
낱말은 `known-acronyms.txt`·`known-terms.txt`, 비교로 인정하는 말은 `baseline-words.txt`.
도메인 용어가 계속 걸리는데 그 분야에서 상식이라면 그 파일에 한 줄 추가한다. 코드를 고치지 않는다.

**스크립트가 조용한 것이 잘 썼다는 뜻은 아니다.** 1번·2번·4번(용어의 뜻, 중간 단계, 문제 설정)은
기계가 못 본다. 스크립트는 빠진 자리를 가리킬 뿐이고, 사슬이 이어졌는지는 직접 읽어서 확인한다.

## 자동 검사

`hooks/py/prose-check.py` 가 PostToolUse 로 돈다. 위키 페이지(`<루트>/<주제>/wiki/**/*.md`)를
쓰면 경고만 뽑아서 보여주고, 그 밖의 파일이면 즉시 끝낸다. 막지 않는다 — 글은 기계가 판정할
대상이 아니라서, 경고는 다시 읽어 볼 자리를 알려 주는 것까지다.

## 다른 규칙과의 경계

겹쳐 쓰지 않는다. 같은 내용이 두 곳에 있으면 어느 쪽이 정본인지 알 수 없게 된다.

| 무엇을 정하나 | 어디 |
|---|---|
| **무엇을** 담을지 (결론 먼저, 용어 정의, 숫자 맥락) | CLAUDE.md §0-2 |
| **분석 결과** 보고의 여섯 단계 (데이터·방법·용어·결과·판단) | `reporting.md` |
| **코드 작업** 보고의 여섯 단계 (결과·변경·검증·제약) | 이 스킬 → `references/work-report.md` |
| 위키 밖 문서의 뼈대 (README·Architecture·API 등) | 이 스킬 → `references/document-structure.md` |
| 위키 페이지의 구조와 index·log 규약 | `llm-wiki-docs` 스킬 |
| **프로젝트 문서와 위키 페이지의 경계** | `llm-wiki-docs` 스킬 |
| 숫자를 말할 자격 (조건표·근거 파일) | `stable-claims.md` |
| 쓰면 안 되는 말투 (이모지·자화자찬) | `output-style.md` |
| **어떻게** 쓸지 — 문장과 생략 | 이 스킬 |

## 하지 말 것

- 용어를 뜻 없이 던지기
- 숫자와 결론만 붙여 놓고 중간 단계를 생략하기
- 비교 기준 없는 숫자
- 주어 없는 문장
- 전문 단위를 일상어로 바꾸지 않기
- 길잡이 문장 없는 표
- 연결어미로 문장 끝내기
- 이중 수동·번역투
- 결론을 맨 뒤에 숨기기
- 스크립트가 조용하다고 다 됐다고 보기
