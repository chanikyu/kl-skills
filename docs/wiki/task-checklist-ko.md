[English](task-checklist.md) · **한국어** · [日本語](task-checklist-ja.md) · [中文](task-checklist-zh.md) · [Español](task-checklist-es.md)

[홈](Home-ko.md) · [설치](Installation-ko.md) · [작동 방식](How-it-works-ko.md)

# task-checklist

일을 시작하기 전에 모든 지시를 체크리스트로 바꾼다. 모든 항목이 끝났거나 이유를 달고 닫혔을 때만 마친다.

## Claude 에서 쓰기

따로 말할 것은 없다. `checklist-start` 게이트가 메시지마다 체크리스트를 요청한다.

## 하는 일

1. 메시지 전체를 읽는다. 번호 붙은 항목, 문장 속에 묻힌 요청, 사용자가 이미 내린 결정까지 본다.
2. 확인할 수 있는 항목으로 나눈다. "테스트를 개선한다" 보다 "테스트가 통과한다" 처럼 쓴다. 메시지 안의 질문도 항목이다.
3. 세션의 체크리스트에 한 줄에 하나씩 쓴다: `- [ ] item`.
4. 항목이 끝나면 바로 `- [x]` 로 표시한다. 할 수 없는 항목은 `- [~] item — reason` 으로 닫는다.
5. 끝내기 전에 목록을 다시 연다. 아직 `- [ ]` 인 것을 마저 끝낸다.

## 파일과 스크립트

```text
~/.claude/checklists/<session>.md        this instruction's list
~/.claude/checklists/<session>.prev.md   the previous instruction's list, kept
```

`KL_CHECKLIST_DIR` 로 폴더를 옮긴다.

## 받쳐 주는 훅

`checklist-start` 는 이전 목록을 옆으로 치워 두고, 새 목록을 어디에 쓸지 알려 준다.
`checklist-check` 는 목록이 없거나 열린 항목이 남아 있으면 답을 한 번 되돌려 보낸다.

## 한계

게이트는 항목에 표시가 됐는지만 본다. 표시 뒤의 일을 잘 했는지는 보지 않는다.

---

[kl-skills](../../README.md) · MIT 라이선스 · [Claude Code](https://claude.com/claude-code) 용으로 만듦
