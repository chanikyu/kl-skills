"""Read a Claude Code or Codex transcript (JSONL) and tell the person's messages from machine text.

Shared by the answer-check gate and the hook-replay skill, so both decide "who wrote
this line" the same way. Two copies of this rule would drift apart, and the replay
would stop showing what the gate really does.
"""

import json

# 코덱스 기록(rollout JSONL)은 끝난 일을 event_msg → item_completed → item 으로 정리해 남긴다.
# 사람 메시지(UserMessage), 답(AgentMessage), 명령(CommandExecution), 파일 변경(FileChange)이 다 있다.
# 코덱스 공식 문서는 기록 형식이 바뀔 수 있다고 한다 — 모양이 다르면 아무것도 읽지 않고 통과시킨다.
CODEX_TEXT_ITEMS = {"UserMessage": "user", "AgentMessage": "assistant"}


def codex_item(entry):
    """코덱스 기록 한 줄이 끝난 일(item_completed)이면 그 item. 아니면 None."""
    payload = entry.get("payload") if entry.get("type") == "event_msg" else None
    if not isinstance(payload, dict) or payload.get("type") != "item_completed":
        return None
    item = payload.get("item")
    return item if isinstance(item, dict) else None


def codex_turn(item):
    """코덱스의 사람 메시지·답 item → (역할, 글). 글이 없으면 None."""
    role = CODEX_TEXT_ITEMS.get(item.get("type"))
    content = item.get("content")
    if not role or not isinstance(content, list):
        return None
    text = "\n".join(block.get("text", "") for block in content
                     if isinstance(block, dict) and isinstance(block.get("text"), str))
    return (role, text) if text.strip() else None


def codex_tool_calls(item):
    """코덱스의 명령·파일 변경 item 을 Claude Code 도구 호출 모양 [(이름, 입력)] 으로 바꾼다.

    answer-check 는 Claude Code 이름(Bash, Edit)으로 이번 턴에 한 일을 판단한다. 같은 판단을 두 벌
    두지 않으려고, 코덱스 기록을 그 모양으로 옮겨 준다. 지운 파일은 남은 결과물이 없어서 뺀다.
    """
    if item.get("type") == "CommandExecution":
        command = item.get("command")
        # ["/bin/zsh", "-lc", "실제 명령"] 처럼 셸을 거친 꼴이면 마지막 칸이 실제 명령이다.
        text = command[-1] if isinstance(command, list) and command else command
        return [("Bash", {"command": text})] if isinstance(text, str) else []
    if item.get("type") == "FileChange" and isinstance(item.get("changes"), dict):
        calls = []
        for path, change in item["changes"].items():
            change = change if isinstance(change, dict) else {}
            if change.get("type") == "delete":
                continue
            moved = change.get("move_path")
            calls.append(("Edit", {"file_path": moved if isinstance(moved, str) and moved else path}))
        return calls
    return []


def typed_by_person(entry, content, text):
    """이 기록 줄이 사람이 직접 쓴 메시지인가.

    기록에서 역할이 user 인 줄에는 사람 글 말고도 기계가 넣은 글이 섞여 있다 — 규칙 묶음,
    대화 요약문, 훅 피드백, 도구 결과. 2026-11-11 에 이것들을 사람 메시지로 세서, 한 번만
    요청한 사람을 "같은 것을 다시 물었다" 고 막았다. 요즘 기록은 사람 글에 origin.kind 를
    "human" 으로 적어 둔다. 그 표시가 없는 옛 기록에서는 기계 글의 생김새로 뺀다.
    """
    origin = entry.get("origin")
    if isinstance(origin, dict):
        return origin.get("kind") == "human"
    if entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    if isinstance(content, list) and any(isinstance(block, dict) and block.get("type") == "tool_result"
                                         for block in content):
        return False
    # <system-reminder> 같은 태그로 시작하는 글도 기계가 넣은 것이다. 이 생김새 판단은 표시가
    # 없을 때만 쓴다 — 표시가 있으면, 사람이 붙여 넣은 "<div> ..." 도 사람 말이다.
    return not text.lstrip().startswith("<")


def classify_line(line):
    """기록 한 줄을 (역할, 글) 로. 대화 사건이 아니거나 글이 없으면 None.

    역할은 "user"(사람이 쓴 글), "machine"(user 자리에 기계가 넣은 글), "assistant" 셋이다.
    """
    try:
        entry = json.loads(line)
    except ValueError:
        return None
    # 줄이 JSON 이어도 객체가 아닐 수 있다(null, 목록). 그런 줄은 사건이 아니라 건너뛴다.
    if not isinstance(entry, dict):
        return None
    item = codex_item(entry)
    if item is not None:
        return codex_turn(item)
    if not isinstance(entry.get("message"), dict):
        return None
    message = entry["message"]
    role = message.get("role")
    if role not in ("user", "assistant"):
        return None
    # 내용은 문자열이거나 블록 목록이다. 블록 중 글(text)만 모으는 이유는,
    # 도구 호출·결과까지 합치면 답변이 아니라 작업 기록을 검사하게 되기 때문이다.
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(block.get("text", "") for block in content
                         if isinstance(block, dict) and block.get("type") == "text")
    else:
        text = ""
    if not text.strip():
        return None
    if role == "user" and not typed_by_person(entry, content, text):
        role = "machine"
    return role, text


def read_turns(transcript_path):
    """대화 기록에서 (역할, 글) 목록을 순서대로. 기록이 없으면 빈 목록."""
    turns = []
    try:
        # 기록은 한 줄에 한 사건인 JSONL 이다. 중간에 깨진 줄이 있어도 나머지는 읽는다.
        with open(transcript_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                turn = classify_line(line)
                if turn:
                    turns.append(turn)
    except OSError:
        return []
    return turns


def tool_calls_since_last_human(transcript_path):
    """마지막 사람 메시지 뒤에 assistant 가 부른 도구들 [(이름, 입력)]. 이번 턴에 한 일이다."""
    calls = []
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                turn = classify_line(line)
                # 사람 메시지가 나오면 새 턴이다. 앞 턴의 도구 호출은 버린다.
                if turn and turn[0] == "user":
                    calls = []
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                item = codex_item(entry) if isinstance(entry, dict) else None
                if item is not None:
                    calls.extend(codex_tool_calls(item))
                    continue
                message = entry.get("message") if isinstance(entry, dict) else None
                if not isinstance(message, dict) or message.get("role") != "assistant":
                    continue
                content = message.get("content")
                for block in content if isinstance(content, list) else []:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_input = block.get("input")
                        calls.append((block.get("name", ""), tool_input if isinstance(tool_input, dict) else {}))
    except OSError:
        return []
    return calls
