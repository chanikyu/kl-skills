[English](research-to-wiki.md) · **한국어** · [日本語](research-to-wiki-ja.md) · [中文](research-to-wiki-zh.md) · [Español](research-to-wiki-es.md)

[홈](Home-ko.md) · [설치](Installation-ko.md) · [작동 방식](How-it-works-ko.md)

# research-to-wiki

조사 요청을 위키 페이지로 바꾼다. 이 페이지는 주장마다 얼마나 확실히 밝혀졌는지 보여 준다.

## Claude 에서 쓰기

"X 가 Y 의 원인인지 조사해줘" 나 "X 의 근거를 찾아줘" 라고 말한다. 조사 요청이면 `skill-match` 가 이 스킬 이름을 알려 준다.

## 하는 일

1. 먼저 위키를 검색한다. 있던 페이지가 있으면 그 페이지를 고치고, 새로 만들지 않는다.
2. 문헌에서 질문의 양쪽 근거를 찾는다. 교란 요인(= 겉보기 관계를 만들어 내는 제3의 원인)도 찾는다.
3. 출처 줄마다 끝에 라벨 두 개를 붙인다. 하나는 연구 종류다(메타분석, 무작위시험, 추적관찰, 유전분석, 단면비교, 동물실험, 세포실험, 리뷰, 의견).
   다른 하나는 얼마나 읽었는지다(본문, 초록, 검색요약). 검사기는 데이터 파일에 적힌 이 이름을 읽으므로 그대로 쓴다.
4. 페이지는 결론을 맨 앞에 두고 자기 말로 쓴다. 숫자는 비교 대상 옆에 둔다.
5. 검사한 다음 위키 목차와 기록에 올린다.

## 파일과 스크립트

| 스크립트 | 하는 일 |
| --- | --- |
| `check_research.py <page>` | 결론이 없는 페이지, 링크나 라벨이 없는 출처, 출처 없는 인용을 알린다 |

라벨 이름은 데이터 파일(`data/evidence-levels.tsv`, `data/reading-levels.txt`)에 있다. 페이지 틀은 `assets/research-page-template.md` 다.

## 한계

검사는 라벨이 있는지만 보고, 맞는지는 보지 않는다. 그건 여전히 논문을 읽어야 안다.

---

[kl-skills](../../README.md) · MIT 라이선스 · [Claude Code](https://claude.com/claude-code) 용으로 만듦
