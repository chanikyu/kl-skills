---
name: task-checklist
description: Turn every instruction into a checklist before working, keep it up to date while working, and finish only when every item is done or explicitly closed. Read the whole message, split it into verifiable items (each request, each decision the person made, each implied check such as tests or a report), write them to the session's checklist file as "- [ ] item", mark "- [x]" as each is done, "- [~] item — reason" when it cannot be done, and compare the list against what was actually done before ending. A Stop hook (checklist-check) blocks the answer once if the list is missing or has open items. Use this for every instruction, especially numbered multi-part requests where one part is easy to drop. Triggers - checklist, todo, to-do, all done, every item, did you finish, 체크리스트, 할 일 목록, 다 했어, 빠진 거 없어, 전부 완료, 지시사항 확인, 항목별로.
---

# Task Checklist

여러 가지를 한 번에 시키면 하나가 조용히 빠진다. 빠진 것은 보고에도 안 나온다 — 한 일만 적기
때문이다. 그래서 일을 시작하기 **전에** 지시를 항목으로 쪼개 적고, 끝내기 전에 그 목록과 대조한다.
2026-11-13 사용자 요청으로 만들었다: "지시문을 분석하고, 체크리스트를 만들어 작업한 뒤, 전부 완료됐는지
확인하고, 완료되지 않은 부분은 진행한다."

## 순서

1. **지시를 끝까지 읽는다.** 번호가 붙은 항목, 문장 속에 묻힌 요청("~도 해줘"), 앞서 사용자가 정한 것
   (질문에 대한 답)을 모두 찾는다
2. **항목으로 쪼갠다.** 한 항목은 "했다/안 했다"를 가릴 수 있어야 한다
   - 나쁨: "README 개선" — 언제 끝났는지 모른다
   - 좋음: "README 스킬 표를 위키 링크로 바꾼다", "README 검사 통과"
   - 질문이 들어 있으면 "질문에 답한다: …" 도 항목이다. 답을 빼먹기 가장 쉽다
   - 확인 작업도 항목이다: 테스트, 실제로 돌려 보기, 보고
3. **파일에 쓴다.** 메시지를 받을 때 훅(`checklist-start`)이 경로를 알려 준다
   (`~/.claude/checklists/<세션>.md`). 한 줄에 하나:

   ```markdown
   - [ ] 2-a 체크리스트 게이트 추가
   - [ ] 2-b 테스트: 미완료면 막는다
   - [ ] 질문 답: 스킬은 자동 적용되나
   ```

4. **하면서 고친다.** 끝낸 항목은 바로 `- [x]` 로 바꾼다. 몰아서 바꾸지 않는다 — 중간에 끊기면 무엇이
   남았는지 안 보인다. 하다가 새로 할 일이 생기면 항목을 더한다
5. **할 수 없는 항목은 닫되 이유를 단다.** `- [~] 항목 — 이유` (사용자 결정이 필요하다, 권한이 없다,
   도구가 없다). 답에도 그대로 밝힌다. 조용히 지우지 않는다
6. **끝내기 전에 대조한다.** 목록을 다시 열어 `- [ ]` 가 남았는지 본다. 남았으면 마저 한다.
   `[x]` 로 표시한 항목은 정말 했는지 — 파일·테스트·출력으로 — 확인한다

## 훅이 하는 일

- `checklist-start` (메시지를 받을 때): 지난 지시의 목록을 `<세션>.prev.md` 로 치우고, 새 목록을 쓸
  경로를 알린다. 지난 턴의 미완료 항목이 이번 답을 막지 않게 하려는 것이다
- `checklist-check` (답이 끝날 때): 목록이 없거나 `- [ ]` 가 남았으면 **한 번** 돌려보낸다. 돌려받으면
  남은 항목을 마저 하거나 `[~]` 로 닫는다. 두 번째에는 막지 않고 남은 것을 알리기만 한다

## 보고

마지막 답에서 목록과 한 일을 맞춘다. `[~]` 로 닫은 항목은 "하지 못한 것"으로 따로 적는다
(natural-answering 의 작업 보고 6단계에서는 "문제 및 제약" 자리).
