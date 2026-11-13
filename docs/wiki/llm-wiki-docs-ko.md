[English](llm-wiki-docs.md) · **한국어** · [日本語](llm-wiki-docs-ja.md) · [中文](llm-wiki-docs-zh.md) · [Español](llm-wiki-docs-es.md)

[홈](Home-ko.md) · [설치](Installation-ko.md) · [작동 방식](How-it-works-ko.md)

# llm-wiki-docs

알게 된 것을 `~/llm-wiki-docs/<topic>/wiki/` 아래의 위키에 남긴다. 주제 하나에 한 페이지를 쓴다.
페이지는 원문을 베끼지 않고 자기 말로 쓰며, 목차와 기록이 함께 있다.

## Claude 에서 쓰기

"이거 위키에 정리해줘" 나 "위키에 저장해줘" 라고 말한다. 메시지가 이 스킬을 부탁하면 `skill-match` 가 스킬 이름을 알려 준다.
Claude 는 남길 만한 조사나 분석을 한 뒤에도 이 스킬을 쓴다.

## 하는 일

1. 출처(= 원래 자료)는 `raw/` 에 그대로 둔다. 위키 페이지는 새로 쓴 글이고, 출처를 고친 글이 아니다.
2. 주제 하나는 페이지 하나다. 같은 주제면 거의 같은 새 페이지를 만들지 않고, 있던 페이지를 고친다.
3. `index.md` 에는 페이지마다 한 줄씩 적는다. 찾을 때는 이 파일을 먼저 본다.
4. `log.md` 는 뒤에 덧붙이기만 하고 고치지 않는다(append-only): `## [YYYY-MM-DD] ingest | title`.
5. 페이지끼리는 `[[page]]` 로 잇는다. 모든 주장은 그 출처를 가리킨다.

코드가 바뀌면 함께 바뀌는 내용은 프로젝트 자체 문서에 둔다. 계속 참인 내용은 위키에 둔다.

## 파일과 스크립트

```text
~/llm-wiki-docs/<topic>/
  README.md      what the topic holds and where things go
  raw/           sources, untouched
  wiki/          pages, index.md, log.md
```

| 스크립트 | 하는 일 |
| --- | --- |
| `new-topic.sh <topic> ["description"]` | 폴더와 빈 목차, 빈 기록을 만든다. 있던 것은 덮어쓰지 않는다 |
| `index-add.py <topic> <page> <category> ["summary"]` | 목차에 페이지를 더한다 |
| `log-append.py <topic> ingest\|query\|lint "title" [--pages --source --note]` | 기록을 한 줄 덧붙인다 |
| `lint.py [topic]` | 목차나 기록에 빠진 페이지, 끊어진 링크, 고아 페이지(= 어떤 페이지도 가리키지 않는 페이지)를 찾는다 |

`LLM_WIKI_ROOT` 환경 변수(= 프로그램 밖에서 넘겨주는 설정값)로 위키의 맨 위 폴더를 `~/llm-wiki-docs` 밖으로 옮긴다.

## 받쳐 주는 훅

`wiki-index-check` 는 목차에 빠진 페이지를 알린다. `wiki-graph` 는 그래프를 다시 그린다.
`prose-check` 는 읽기 어려운 자리를 알린다. `wiki-sync` 는 답이 끝날 때 셸(= 명령을 직접 치는 창)에서 고친 페이지를 잡아낸다.

## 한계

위키는 사용자의 컴퓨터에만 있다. 다른 곳으로 동기화해 주는 기능은 없다.

---

[kl-skills](../../README.md) · MIT 라이선스 · [Claude Code](https://claude.com/claude-code) 용으로 만듦
