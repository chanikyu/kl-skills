#!/usr/bin/env python3
"""PostToolUse gate: a wiki page was just written, so look for omissions in it.

Runs natural-answering's checker and prints only the warn-grade findings. It never
blocks: prose is not a thing a machine can judge, so the most a hook should do is
point at the places worth re-reading.

index.md and log.md are skipped. They are catalogs of one-line entries, where the
rules this checker enforces (a subject in every sentence, a lead-in before a table)
do not apply.

A hook must never break a session, so every failure path here exits 0.
"""

import json
import os
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKER = os.path.join(PLUGIN_ROOT, "skills", "natural-answering", "scripts", "check_prose.py")
SKIP = {"index.md", "log.md"}
LIMIT = "6"  # ponytail: 한 번에 6건까지만. 더 보려면 스크립트를 직접 돌린다.


def wiki_page(path, root):
    if not path or not path.endswith(".md"):
        return False
    if os.path.basename(path) in SKIP:
        return False
    try:
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(root))
    except (OSError, ValueError):
        return False
    parts = rel.split(os.sep)
    return len(parts) >= 3 and parts[0] not in ("..", ".") and parts[1] == "wiki"


def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return 0

    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    root = os.environ.get("LLM_WIKI_ROOT") or os.path.join(os.path.expanduser("~"), "llm-wiki-docs")

    if not wiki_page(path, root) or not os.path.isfile(CHECKER) or not os.path.isfile(path):
        return 0

    try:
        out = subprocess.run(
            [sys.executable, CHECKER, "--exit-zero", "--limit", LIMIT, path],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return 0

    text = (out.stdout or b"").decode("utf-8", "replace").strip()
    # 마지막 줄은 집계다. 그 줄만 남았으면 경고가 없다는 뜻이므로 아무 말도 하지 않는다.
    if out.returncode == 0 and len(text.splitlines()) > 1:
        print(text)
        print("(natural-answering: 다시 읽어 볼 자리다. 막지는 않는다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
