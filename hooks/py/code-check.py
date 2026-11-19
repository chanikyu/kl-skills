#!/usr/bin/env python3
"""PostToolUse gate: a code file was written, so look at its names and comments.

Python, and every language listed in skills/readable-code/data/languages.json. A Python file
is also given to the no-hardcoding checker: machine-only absolute paths and long tables of
values written into the code. Before 2026-11-19 nothing checked those — readable-code left
them to the no-hardcoding skill, which was a document only.

Reports only. Names and comments are not a thing a machine should block on — the
checker can see that a name is two letters long, but not whether a longer one
would be a lie. So the most this does is point at the lines worth a second look.

Paths that are not the user's own code are skipped: caches, virtualenvs, vendored
packages and scratch directories. A gate that nags about site-packages gets
switched off, and then it is not protecting anything.
"""

import json
import os
import subprocess
import sys

from _hook_output import read_payload, tell_model
from _work_files import is_not_own_code, is_skipped

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKER = os.path.join(PLUGIN_ROOT, "skills", "readable-code", "scripts", "check_code.py")
LANGUAGES = os.path.join(PLUGIN_ROOT, "skills", "readable-code", "data", "languages.json")
HARDCODING = os.path.join(PLUGIN_ROOT, "skills", "no-hardcoding", "scripts", "check_hardcoding.py")
LIMIT = "6"   # ponytail: 검사기마다 한 번에 6건까지. 전부 보려면 검사기를 직접 돌린다.


def checked_extensions():
    """검사기가 읽는 확장자들. 파이썬과, 규칙 파일에 적힌 다른 언어들.

    모든 파일마다 검사기를 띄우지 않으려고 여기서 먼저 거른다. 규칙 파일을 못 읽으면
    파이썬만 본다 — 예전과 같은 동작이다.
    """
    extensions = {".py"}
    try:
        with open(LANGUAGES, encoding="utf-8") as handle:
            for language in json.load(handle).get("languages", []):
                extensions.update(ext.lower() for ext in language.get("extensions", []))
    except (OSError, ValueError, AttributeError):
        pass
    return extensions


def own_code_file(path):
    """사용자가 직접 쓴, 검사기가 읽는 언어의 파일인가."""
    if not path or os.path.splitext(path)[1].lower() not in checked_extensions():
        return False
    return not is_skipped(path) and not is_not_own_code(path)


def run_checker(checker, file_path):
    """검사기 하나를 돌려 지적이 있으면 그 글을, 없거나 돌지 못하면 빈 글을 준다."""
    if not os.path.isfile(checker):
        return ""
    try:
        finished = subprocess.run(
            # --changed: 옛 이름·옛 값까지 지적하면 "김에" 고치게 된다. git 밖 파일·새 파일은 전부 본다.
            [sys.executable, checker, "--exit-zero", "--changed", "--limit", LIMIT, file_path],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    report = (finished.stdout or b"").decode("utf-8", "replace").strip()
    # 마지막 줄은 집계다. 그 줄만 남았으면 지적이 없다는 뜻이므로 아무 말도 하지 않는다.
    return report if finished.returncode == 0 and len(report.splitlines()) > 1 else ""


def main():
    """게이트 본체. 어떤 경우에도 0으로 끝낸다 — 훅이 터지면 그 사건이
    걸린 모든 세션이 깨진다.
    """
    raw_payload = read_payload()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0

    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not own_code_file(file_path) or not os.path.isfile(file_path):
        return 0

    parts = []
    names = run_checker(CHECKER, file_path)
    if names:
        parts.append(names + "\n(readable-code: 이름과 설명을 다시 볼 자리다. 막지는 않는다."
                             " 손대지 않은 줄은 고치지 말고 알리기만 한다)")
    values = run_checker(HARDCODING, file_path) if file_path.endswith(".py") else ""
    if values:
        parts.append(values + "\n(no-hardcoding: 값을 코드 밖으로 뺄 자리다. 막지는 않는다."
                              " 손대지 않은 줄은 고치지 말고 알리기만 한다)")
    if parts:
        tell_model("PostToolUse", "\n\n".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
