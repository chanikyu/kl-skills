[English](graph-doc-memory.md) · **한국어** · [日本語](graph-doc-memory-ja.md) · [中文](graph-doc-memory-zh.md) · [Español](graph-doc-memory-es.md)

[홈](Home-ko.md) · [설치](Installation-ko.md) · [작동 방식](How-it-works-ko.md)

# graph-doc-memory

위키 전체를 그래프 데이터베이스(= 점과 선으로 이어진 자료 저장소) 하나로 바꾼다.
그리고 브라우저에서 움직여 볼 수 있는 그래프로 연다. 부탁할 때만 한다.

## Claude 에서 쓰기

"위키 그래프 보여줘" 라고 말한다.

## 하는 일

1. `<topic>/wiki/` 아래의 페이지는 모두 노드(= 그래프의 점)가 된다. `[[link]]` 와 `[text](page.md)` 는 모두 링크(= 점을 잇는 선)가 된다.
   아직 없는 페이지로 가는 링크도 그래프에 점선 원으로 남는다. 채울 만한 빈자리라는 뜻이다.
2. 그래프를 만들면 두 파일이 생긴다. `~/llm-wiki-docs/.graph/graph.json` 과, 다른 파일 없이 혼자 열리는 `viewer.html` 이다.
   `viewer.html` 은 서버(= 웹 페이지를 보내 주는 프로그램) 없이 `file://` 로 열린다.
3. 뷰어(= 그래프를 보는 화면)에는 검색이 있다. 고아 페이지(= 아무 링크도 받지 못한 페이지)와 없는 페이지를 켜고 끌 수 있다.
   노드 크기, 링크 굵기, 네 가지 힘(= 점끼리 당기고 밀어 자리를 잡는 힘)을 조절한다. 고른 노드 주변만 보는 로컬 그래프도 있다.
   노드를 누르면 경로, 링크, 백링크(= 이 페이지를 가리키는 다른 페이지)가 보인다.

## 파일과 스크립트

| 스크립트 | 하는 일 |
| --- | --- |
| `open-graph.sh [--root DIR] [--out DIR] [--no-build]` | 그래프를 다시 만들고 뷰어를 연다 |
| `build_graph.py [--root ROOT] [--out OUT] [--quiet]` | 열지 않고 다시 만들기만 한다 |

## 받쳐 주는 훅

`wiki-graph` 는 위키 페이지가 쓰일 때 그래프를 다시 만든다. `wiki-sync` 는 답이 끝날 때 셸(= 명령을 직접 치는 창)에서 고친 것을 잡아낸다.

## 한계

저절로 열리는 일은 없다. 그래프가 얼마나 잘 이어지는지는 페이지들의 링크에 달려 있다.

---

[kl-skills](../../README.md) · MIT 라이선스 · [Claude Code](https://claude.com/claude-code) 용으로 만듦
