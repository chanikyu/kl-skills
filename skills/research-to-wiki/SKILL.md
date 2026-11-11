---
name: research-to-wiki
description: Turn a literature or web research request into a wiki page that shows how far each claim is established - search the wiki first, search the literature, fetch each paper's identifiers, label every source with what kind of study it is (randomized trial, cohort, Mendelian randomization, cross-sectional, animal, cell, review, opinion) and how much of it was read (full text, abstract, search summary), write the page in your own words with the conclusion first, check it with scripts/check_research.py, register it in the wiki index and log, then answer the person briefly with citations. Use for any request to research, investigate, look up evidence on, or summarize the literature about a question - especially cause-or-effect questions where an animal study can be mistaken for human evidence. Triggers - research, literature review, look up papers, evidence for, cause or consequence, PubMed, Consensus, 리서치, 조사해줘, 문헌 조사, 논문 찾아줘, 근거가 뭐야, 원인인지 결과인지, 연구 정리.
---

# Research to Wiki

조사 결과를 대화에만 남기면 다음 세션은 처음부터 다시 찾는다. 그래서 위키에 남긴다. 그런데
위키에 남길 때 두 가지가 쉽게 빠진다.

1. **그 근거가 어떤 연구인가.** 쥐 실험과 사람 시험이 같은 무게로 적히면 결론이 부풀려진다.
   2026-11-11 장내 미생물 조사에서, 사람 대변을 쥐에 옮긴 연구의 95%가 "병이 옮았다"고
   보고했다. 이 숫자를 사람 증거처럼 쓰면 틀린 결론이 된다
2. **내가 어디까지 읽었나.** 초록만 읽고 쓴 숫자를 본문에서 확인한 것처럼 옮기게 된다

이 스킬은 출처마다 그 두 가지를 적게 하고, 빠지면 검사가 잡는다.

## 순서

1. **위키부터** — `wiki-recall` 이 붙여 준 페이지가 있으면 연다. 같은 주제 페이지가 있으면
   새로 만들지 않고 그 페이지를 고친다(한 주제 = 한 페이지)
2. **문헌 검색** — Consensus·PubMed 같은 검색 도구로 찾는다. 질문의 양쪽을 따로 찾는다
   (원인 쪽 근거, 결과 쪽 근거, 교란). 한쪽만 찾으면 한쪽 결론만 나온다
3. **논문 정보 확인** — 핵심 논문은 DOI 까지 받는다. 검색 요약으로만 본 논문은 그렇다고 적는다
4. **출처마다 두 표시** — 출처 줄 끝에 `— <근거 수준> · <읽은 수준>`
   - 근거 수준 이름: `data/evidence-levels.tsv` (메타분석, 무작위시험, 추적관찰, 유전분석,
     단면비교, 동물실험, 세포실험, 리뷰, 의견)
   - 읽은 수준 이름: `data/reading-levels.txt` (본문, 초록, 검색요약)
5. **페이지 쓰기** — `assets/research-page-template.md` 를 따른다
   - 맨 앞은 결론 한두 문장. 질문의 낱말로 답한다. "둘 다다", "아직 모른다"도 결론이다
   - 내 말로 다시 쓴다. 숫자는 비교 대상과 함께 쓴다 (16명 중 13명 vs 13명 중 4명)
   - 내 판단은 "내 판단이다"라고 적어 문헌의 말과 섞지 않는다
6. **검사** — `python3 scripts/check_research.py <페이지>` 를 돌려 지적이 0건이 될 때까지 고친다
7. **위키 등록** — `llm-wiki-docs` 의 `new-topic.sh`(새 주제일 때), `index-add.py`, `log-append.py`
8. **답하기** — `natural-answering` 대로. 결론 한 문장 → 근거 몇 줄 → 페이지 경로.
   검색 도구가 요구하는 인용 표기(DOI 링크, 번호 인용, 안내 문구)는 빼지 않는다

## 검사가 보는 것

| 코드 | 뜻 |
|---|---|
| `conclusion-not-first` | 제목 다음이 결론 문장이 아니라 목록·표·소제목이다 |
| `missing-sources` | `## 출처` 절이 없다 |
| `source-missing-link` | 출처에 DOI·주소가 없다 |
| `source-missing-levels` | 출처 끝에 근거 수준·읽은 수준이 없다 |
| `unknown-evidence-level` / `unknown-reading-level` | 목록에 없는 이름을 썼다 |
| `citation-without-source` | 본문의 [저자 연도] 가 출처 목록에 없다 |
| `source-not-cited` | 출처 목록에만 있고 본문에서 인용하지 않았다 |

검사는 표시가 **있는지**만 본다. 표시가 **맞는지**(정말 무작위시험인지)는 논문을 보고 사람이 판단한다.
