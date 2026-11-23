"""Where a session's checklist lives and how to read it.

Shared by checklist-start (UserPromptSubmit) and checklist-check (Stop), so both
agree on the path and on what counts as an open item.

Item marks, one item per line:
  - [ ] item            open — still to do
  - [x] item            done
  - [~] item — reason   closed without doing it (blocked, or the person said not to); the answer says why
"""

import os
import re
import tempfile

CHECKLIST_DIR_ENV = "KL_CHECKLIST_DIR"
# 코덱스는 플러그인 훅에 PLUGIN_ROOT 를 넘기고(openai/codex codex-rs/hooks/src/engine/discovery.rs),
# Claude Code 는 CLAUDE_PLUGIN_ROOT 만 넘긴다. 그래서 이 변수로 '코덱스에서 도는가' 를 가린다.
CODEX_MARKER_ENV = "PLUGIN_ROOT"
# 줄 안의 빈칸만 본다([ \t]): \s 는 줄바꿈까지 먹어서, 내용 없는 '- [ ]' 가 다음 줄과 붙거나 아예 안 잡혔다.
OPEN_ITEM = re.compile(r"^[ \t]*[-*][ \t]*\[ \][ \t]*(.*?)[ \t]*$", re.MULTILINE)
ANY_ITEM = re.compile(r"^[ \t]*[-*][ \t]*\[[ xX~]\]", re.MULTILINE)
ANY_ITEM_TEXT = re.compile(r"^[ \t]*[-*][ \t]*\[[ xX~]\][ \t]*(.*?)[ \t]*$", re.MULTILINE)
HEADING = re.compile(r"^#{1,6}[ \t]+(.*?)[ \t]*$")
CARRIED_HEADING = "넘어온 항목 — "
# 항목의 이름: 확인 방법(→)이나 닫은 이유(—) 앞까지. 끝낼 때 그 뒤에 결과를 덧붙여도 같은 항목으로 본다.
ITEM_NAME_END = re.compile(r"[ \t]+[→—][ \t]")


def checklist_dir():
    """체크리스트를 두는 폴더. 프로젝트 안에 두면 git 에 섞이므로 사용자 폴더에 둔다.

    코덱스에서는 임시 폴더($TMPDIR, 없으면 /tmp) 아래에 둔다. 코덱스 모델이 쓸 수 있는 자리는
    작업 폴더·/tmp·$TMPDIR·설정한 writable_roots 뿐이라(openai/codex protocol/src/protocol.rs
    get_writable_roots_with_cwd), ~/.claude 에 두면 모델이 목록을 못 만들고 checklist-check 가
    끝낼 때마다 막았다(2026-11-20 Capitis 세션, 코덱스 0.171). 훅은 코덱스 환경을 물려받아 같은 $TMPDIR 를 본다.
    """
    configured = os.environ.get(CHECKLIST_DIR_ENV)
    if configured:
        return configured
    if os.environ.get(CODEX_MARKER_ENV):
        return os.path.join(tempfile.gettempdir(), "kl-skills", "checklists")
    return os.path.join(os.path.expanduser("~"), ".claude", "checklists")


def checklist_path(session_id):
    """세션마다 하나. 세션 id 에서 파일 이름에 쓸 수 없는 글자는 뺀다. id 가 없으면 None."""
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", str(session_id or ""))
    return os.path.join(checklist_dir(), safe_id + ".md") if safe_id else None


def carry_path(path):
    """지난 지시에서 넘어온 항목을 적어 두는 파일. 답이 끝날 때 그 항목이 목록에서 사라졌는지 대조한다."""
    return path[:-3] + ".carry.md"


def read_text(path):
    """파일 글 전체. 없거나 못 읽으면 None."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def read_items(path):
    """(안 끝난 항목 목록, 전체 항목 수). 파일이 없거나 못 읽으면 ([], 0)."""
    text = read_text(path)
    if text is None:
        return [], 0
    return OPEN_ITEM.findall(text), len(ANY_ITEM.findall(text))


def item_name(item_text):
    """항목 글에서 이름만: '푸시 → 확인: …' → '푸시', '보고 — 미뤘다' → '보고'."""
    return ITEM_NAME_END.split(item_text, 1)[0].strip()


def item_names(text):
    """목록 글에 있는 모든 항목(끝났든 아니든)의 이름 집합."""
    return {item_name(item) for item in ANY_ITEM_TEXT.findall(text or "")}


def open_items_by_heading(text):
    """안 끝난 항목을 그 위 제목과 함께 [(제목, 항목 글)] 로. 내용 없는 칸은 넘길 것이 없어 뺀다."""
    found, heading = [], "앞선 지시"
    for line in text.splitlines():
        title = HEADING.match(line)
        if title:
            # 두 번 넘어오면 "넘어온 항목 — 넘어온 항목 — …" 으로 쌓이지 않게 원래 제목만 남긴다
            heading = title.group(1).replace(CARRIED_HEADING, "") or heading
            continue
        item = OPEN_ITEM.match(line)
        if item and item.group(1):
            found.append((heading, item.group(1)))
    return found
