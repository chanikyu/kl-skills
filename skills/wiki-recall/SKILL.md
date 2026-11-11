---
name: wiki-recall
description: Pull what the wiki already knows into the answer instead of working it out again. A hook searches ~/llm-wiki-docs every time the user sends a message and attaches the paths and key lines of clearly related pages; this skill is how to go further - read those pages in full, load the whole wiki when it is small (CAG) or only the most relevant pages when it is large (RAG), and follow graph links to the pages next door. Use this whenever a question may already be answered in the wiki, when the hook has attached wiki pages, before researching a topic from scratch, before restating a number or decision that was settled before, and when asked "위키에서 찾아줘 / 전에 정리한 거 / 예전에 뭐라고 했지 / 이미 조사했던 거". Triggers - wiki, recall, retrieve, search notes, RAG, CAG, knowledge base, what did we decide, previous finding, 위키, 위키 검색, 찾아줘, 전에 정리한, 예전 결론, 이미 조사한, 지식 검색, 기억.
---

# Wiki Recall

위키는 한 번 정리한 지식을 다시 쓰려고 만든다. 하지만 **찾아 읽지 않으면 없는 것과 같다.**
이전 세션에서 결론을 낸 주제를 처음부터 다시 조사하는 일이 그렇게 생긴다. 그러면 다른 숫자가
나오고, 같은 함정을 다시 밟는다. 이 스킬은 답하기 전에 위키를 먼저 본다.

## 저절로 일어나는 일

사용자가 메시지를 보낼 때마다 훅이 위키를 검색한다. 관련이 분명한 페이지가 있으면 **경로, 제목,
핵심 줄 두어 개**를 붙여 준다. 관련이 약하면 아무것도 붙이지 않는다.

붙은 것은 단서다. 줄 몇 개는 검색이 고른 일부라서, **인용하거나 숫자를 다시 말하려면 그 페이지를
열어서 확인한다**(`stable-claims.md` R0 — 파일이 있으면 연다).

## 깊게 가져오기 — CAG 와 RAG

```bash
scripts/recall.py "질문"                 # 위키 크기로 자동 선택
scripts/recall.py "질문" --full          # 고른 페이지의 본문 전체까지
scripts/recall.py "질문" --mode rag --top 5
```

| 방식 | 언제 | 무엇을 가져오나 |
|---|---|---|
| CAG (캐시처럼 통째로) | 위키 전체가 3만 자 이하 | 페이지 전부, 관련 순 |
| RAG (골라서) | 그보다 클 때 | 질문을 잘 덮는 페이지 몇 장 + 링크로 이어진 이웃 |

작은 위키를 통째로 읽는 것은 낭비가 아니다. 고르다가 놓칠 일이 없고, 그 정도 분량은 읽을 수
있다. 위키가 커지면 다 읽을 수 없으니 고른다. 기준 글자 수는 `--cag-max-chars` 로 바꾼다.

## 어떻게 찾나

- 한국어는 띄어쓰기만으로 낱말이 갈리지 않아서, 두 글자씩 겹쳐 자른 조각으로 비교한다
- 순위는 BM25(문서 검색의 표준 공식)로 매긴다. 드문 조각이 맞을수록 점수가 높다
- **질문을 얼마나 덮는지**를 따로 잰다. 드문 낱말에 무게를 두고, 페이지가 가진 질문 낱말의
  무게를 전체로 나눈다. 위키에 없는 낱말이 많은 질문은 낮게 나온다 — 위키가 모르는 것을 묻는다는
  뜻이다
- 그래프가 있으면 상위 페이지의 이웃도 낮은 점수로 붙인다. 답이 바로 옆 페이지에 있는 일이 많다

## 찾은 뒤에

1. 붙은 페이지 가운데 질문에 맞는 것을 **열어 읽는다**
2. 위키에 답이 있으면 그것으로 답하고, 경로를 출처로 붙인다
3. 위키의 결론과 지금의 판단이 다르면 **다르다고 말한다.** 조용히 새 판단으로 갈아끼우지 않는다
4. 위키에 없던 것을 새로 알게 됐으면 `llm-wiki-docs` 스킬로 위키에 넣는다. 다음 검색에서 찾힌다

## 하지 말 것

- 붙은 줄 몇 개만 보고 숫자나 결론을 인용하기
- 위키에 이미 있는 주제를 처음부터 다시 조사하기
- 위키와 다른 결론을 말하면서 다르다는 사실을 숨기기
- 관련 없는 페이지가 붙었는데 억지로 끌어다 쓰기

## 다른 규칙과의 경계

| 무엇을 정하나 | 어디 |
|---|---|
| 위키에 무엇을 어떻게 쓰나 | `llm-wiki-docs` 스킬 |
| 위키를 그래프로 보기 | `graph-doc-memory` 스킬 (이 스킬은 그 그래프의 링크를 쓴다) |
| 위키에서 찾아 답에 쓰기 | 이 스킬 |
| 숫자를 다시 말하기 전에 파일을 연다 | `stable-claims.md` R0 |
