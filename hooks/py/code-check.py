#!/usr/bin/env python3
"""PostToolUse gate: a python file was written, so look at its names and comments.

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

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKER = os.path.join(PLUGIN_ROOT, "skills", "readable-code", "scripts", "check_code.py")
# 내 코드가 아닌 자리. 여기까지 지적하면 게이트가 꺼진다.
SKIP_PARTS = ("__pycache__", "/.venv/", "/venv/", "/site-packages/", "/node_modules/",
              "/.git/", "/scratchpad/", "/.tox/", "/build/", "/dist/")
LIMIT = "6"   # ponytail: 한 번에 6건까지. 전부 보려면 check_code.py 를 직접 돌린다.


def own_python_file(path):
    """사용자가 직접 쓴 파이썬 파일인가."""
    if not path or not path.endswith(".py"):
        return False
    normalised = path.replace("\\", "/")
    return not any(part in normalised for part in SKIP_PARTS)


def main():
    """게이트 본체. 어떤 경우에도 0으로 끝낸다 — 훅이 터지면 그 사건이
    걸린 모든 세션이 깨진다.
    """
    raw_payload = sys.stdin.read()
    try:
        event = json.loads(raw_payload) if raw_payload.strip() else {}
    except ValueError:
        return 0

    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not own_python_file(file_path):
        return 0
    if not os.path.isfile(CHECKER) or not os.path.isfile(file_path):
        return 0

    try:
        finished = subprocess.run(
            [sys.executable, CHECKER, "--exit-zero", "--limit", LIMIT, file_path],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return 0

    report = (finished.stdout or b"").decode("utf-8", "replace").strip()
    # 마지막 줄은 집계다. 그 줄만 남았으면 지적이 없다는 뜻이므로 아무 말도 하지 않는다.
    if finished.returncode == 0 and len(report.splitlines()) > 1:
        print(report)
        print("(readable-code: 이름과 설명을 다시 볼 자리다. 막지는 않는다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
