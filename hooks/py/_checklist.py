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

CHECKLIST_DIR_ENV = "KL_CHECKLIST_DIR"
# 줄 안의 빈칸만 본다([ \t]): \s 는 줄바꿈까지 먹어서, 내용 없는 '- [ ]' 가 다음 줄과 붙거나 아예 안 잡혔다.
OPEN_ITEM = re.compile(r"^[ \t]*[-*][ \t]*\[ \][ \t]*(.*?)[ \t]*$", re.MULTILINE)
ANY_ITEM = re.compile(r"^[ \t]*[-*][ \t]*\[[ xX~]\]", re.MULTILINE)


def checklist_dir():
    """체크리스트를 두는 폴더. 프로젝트 안에 두면 git 에 섞이므로 사용자 폴더에 둔다."""
    return os.environ.get(CHECKLIST_DIR_ENV) or os.path.join(os.path.expanduser("~"), ".claude", "checklists")


def checklist_path(session_id):
    """세션마다 하나. 세션 id 에서 파일 이름에 쓸 수 없는 글자는 뺀다. id 가 없으면 None."""
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", str(session_id or ""))
    return os.path.join(checklist_dir(), safe_id + ".md") if safe_id else None


def read_items(path):
    """(안 끝난 항목 목록, 전체 항목 수). 파일이 없거나 못 읽으면 ([], 0)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError:
        return [], 0
    return OPEN_ITEM.findall(text), len(ANY_ITEM.findall(text))
