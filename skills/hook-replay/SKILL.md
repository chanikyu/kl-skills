---
name: hook-replay
description: Replay one hook gate against a real Claude Code transcript, at every message the person typed, and record what the gate would have said at that moment. Use after changing a gate that reads the conversation (answer-check, wiki-recall, wiki-sync) and before releasing it - fixtures only hold the conversations their author imagined, while real transcripts carry compaction summaries, rule dumps, resent messages and pasted code. Also use when a gate fired where it should not have, to reproduce the false positive across the whole session instead of one message. Results go to a TSV, one row per moment. Triggers - hook replay, replay transcript, false positive, gate fired wrongly, check the hook on real data, 훅 재생, 훅 다시 돌려, 실제 대화로 확인, 오탐, 잘못 막았다, 훅이 엉뚱하게 떴다.
---

# Hook Replay

훅 테스트는 만든 사람이 **상상한 대화**로 돈다. 실제 대화에는 상상하지 못한 것이 섞여 있다.
2026-11-11 answer-check 가 그랬다 — 테스트는 전부 통과했는데, 실제 기록에는 요약문·규칙
묶음·6초 간격으로 두 번 들어온 같은 메시지가 있었고, 훅은 그것들을 사람 말로 셌다.
그 세션 기록의 메시지 40개에 훅을 다시 돌려 보자 결함이 한꺼번에 드러났다.

이 스킬은 그 일을 명령 한 줄로 한다: **사람 메시지마다, 그 시점의 기록을 잘라 훅에 넘긴다.**

## 언제 쓰나

1. 대화를 읽는 게이트를 고친 뒤, 배포하기 전 — 테스트 통과만으로 끝내지 않는다
2. 게이트가 엉뚱한 곳에서 떴을 때 — 그 한 번이 아니라 세션 전체에서 몇 번 그랬는지 본다

## 쓰는 법

```sh
python3 scripts/replay.py <게이트> --transcript <기록.jsonl> --out <결과.tsv> [--event stop|prompt] [--last N]
```

- 게이트 이름은 `hooks/run.sh` 에 넘기는 이름이다: `answer-check`, `wiki-recall`, `wiki-sync`
- `--event` 는 훅이 도는 순간에 맞춘다
  - `stop` (기본) — 턴이 끝난 시점. 사람 메시지와 그 답까지 잘라 넘긴다. Stop 훅용
  - `prompt` — 메시지를 보낸 시점. 그 메시지는 기록에 없고 `prompt` 로 따로 간다. UserPromptSubmit 훅용
- 지금 세션의 기록은 `~/.claude/projects/<프로젝트 폴더>/<세션 id>.jsonl` 이다
- `--plugin-root` 를 주면 설치본(`~/.claude/plugins/cache/...`)의 훅을 돌린다. 안 주면 이 리포의 훅이다

결과 파일 이름에는 게이트·시점·범위를 넣는다 (`replay_wiki-recall_prompt_all.tsv`).
조건을 바꿔 다시 돌릴 때 앞 결과를 덮어쓰지 않기 위해서다.

## 결과 읽기

화면에는 요약 한 줄과 **훅이 말한 시점**만 나온다. 전체는 TSV 에 있다.

| 열 | 뜻 |
|---|---|
| `turn` | 몇 번째 사람 메시지인가 |
| `fired` | 훅이 무언가 말했나 (`yes`/`no`) |
| `exit_code` | 0 이 아니면 훅이 터진 것이다. 말한 내용보다 먼저 본다 |
| `seconds` | 걸린 시간. 훅 제한 시간에 가까우면 실제 세션에서 잘린다 |
| `message` | 그 시점의 사람 메시지 |
| `output` | 훅이 낸 말 (앞부분) |

말한 시점마다 **그 말이 맞았나**를 사람 메시지와 견줘 판정한다. 틀린 시점이 곧 고칠 자리다.

## 주의

- 위키를 읽는 훅(wiki-recall)은 **지금의 위키**로 돈다. 그 시점의 위키가 아니다.
  나중에 생긴 페이지가 옛 메시지에 붙을 수 있다 — 오탐인지 볼 때 이 점을 뺀다
- 쓰는 훅(wiki-sync 는 그래프를 다시 만든다)은 실제로 파일을 쓴다. 돌리기 전에 무엇을 쓰는지 본다
- POSIX `sh` 로 런처를 부른다. Windows 에서는 돌지 않는다
- 사람 메시지 판정은 훅과 같은 코드(`hooks/py/_transcript.py`)를 쓴다. 따로 고치지 않는다
