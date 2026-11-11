#!/usr/bin/env python3
"""PostToolUse gate: a wiki page was just written, so refresh the graph db.

Claude Code hands this the event payload as JSON on stdin. It fires on every
Write/Edit, so the first thing it does is decide whether the file has anything
to do with a wiki — that check is a few string comparisons, which is what keeps
the gate off the critical path for every other edit in a session.

A hook must never break a session: every failure path here exits 0.

ponytail: rebuilds the whole graph on each wiki write (a few hundred small pages
is tens of milliseconds). If a wiki ever grows big enough for that to be felt,
make the builder incremental — reparse the one changed page and patch graph.json.
"""

import json
import os
import subprocess
import sys

# hooks/py/wiki-graph.py -> hooks/py -> hooks -> the plugin root. Three levels:
# one short and the builder path lands in hooks/skills/, which does not exist.
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDER = os.path.join(PLUGIN_ROOT, "skills", "graph-doc-memory", "scripts", "build_graph.py")


def wiki_page(path, root):
    """True only for <root>/<topic>/wiki/**/*.md."""
    if not path or not path.endswith(".md"):
        return False
    try:
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(root))
    except (OSError, ValueError):
        return False
    parts = rel.split(os.sep)
    return len(parts) >= 3 and parts[0] not in ("..", ".") and parts[1] == "wiki"


def main():
    """위키 페이지가 쓰였으면 그래프를 다시 만든다. 늘 0으로 끝낸다."""
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return 0

    # Bash 로 쓴 경우는 여기 안 걸린다(경로가 payload 에 없다). 그쪽은 wiki-touch 가 본다.
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    root = os.environ.get("LLM_WIKI_ROOT") or os.path.join(os.path.expanduser("~"), "llm-wiki-docs")

    if not wiki_page(path, root):
        return 0
    if not os.path.isfile(BUILDER):
        return 0

    try:
        out = subprocess.run(
            [sys.executable, BUILDER, "--root", root],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return 0

    first = (out.stdout or b"").decode("utf-8", "replace").strip().splitlines()
    if out.returncode == 0 and first:
        print("wiki %s (db: %s)" % (first[0], os.path.join(root, ".graph", "graph.json")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
