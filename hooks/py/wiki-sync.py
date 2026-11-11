#!/usr/bin/env python3
"""Stop gate: bring the graph and the prose check up to date before the session ends.

Why this exists even though two PostToolUse gates already do the same work:
those gates fire on Write/Edit/MultiEdit, and a model often writes files with
Bash instead — a heredoc, `sed`, a small python script. Then nothing fires, the
graph silently falls behind the wiki, and omissions in a page nobody re-read stay
unreported. Observed on 2026-11-11: a session researched a topic and updated its
page, index and log entirely through Bash, so all three gates stayed quiet.

Adding Bash to the PostToolUse matcher would fix it the expensive way. Bash is
the most-used tool, the payload carries a command line rather than a path, and
shell variables inside it cannot be resolved. This gate runs **once per session**
instead and asks the filesystem, which does not care how a file was written:
every page newer than graph.json has changed since the last sync.

graph.json doubles as the marker. Rebuilding it moves its own mtime forward, so
the next session compares against the right point with no bookkeeping to keep.

A hook must never break a session: every failure path exits 0, and this gate
never blocks — it reports.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
BUILDER = PLUGIN_ROOT / "skills" / "graph-doc-memory" / "scripts" / "build_graph.py"
CHECKER = PLUGIN_ROOT / "skills" / "natural-answering" / "scripts" / "check_prose.py"
# 목차와 기록은 한 줄 항목의 목록이라 글 규칙(주어·길잡이 문장)이 적용되지 않는다.
SKIP = {"index.md", "log.md"}
LIMIT = "6"      # ponytail: 한 번에 6건까지. 더 보려면 check_prose.py 를 직접 돌린다.
MAX_PAGES = 20   # 한 세션에 이보다 많이 바뀌면 글 검사는 건너뛴다 — 출력이 보고가 아니라 벽이 된다.


def wiki_root() -> Path:
    env = os.environ.get("LLM_WIKI_ROOT")
    return Path(env) if env else Path.home() / "llm-wiki-docs"


def wiki_pages(root: Path) -> list[Path]:
    """<뿌리>/<토픽>/wiki/**.md 전부. 목차와 기록은 빼고 준다.

    토픽은 wiki/ 를 가진 디렉토리로 정한다. 숨은 디렉토리(.graph 등)는 토픽이 아니다.
    """
    out: list[Path] = []
    try:
        topics = sorted(entry for entry in root.iterdir()
                        if not entry.name.startswith(".") and (entry / "wiki").is_dir())
    except OSError:
        return out
    for topic in topics:
        for path in sorted((topic / "wiki").rglob("*.md")):
            if path.name not in SKIP and not path.name.startswith("."):
                out.append(path)
    return out


def run(cmd: list[str]) -> str:
    """다른 스크립트를 돌려 그 출력만 돌려준다. 실패하면 빈 문자열이다.

    실패를 예외로 올리지 않는 것은 훅이기 때문이다. 한 스크립트가 없다고 세션을
    끝내지 못하게 만들면, 규칙이 지켜지는 대신 작업이 멈춘다.
    """
    try:
        finished = subprocess.run(cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return ""
    return (finished.stdout or b"").decode("utf-8", "replace").strip()


def main() -> int:
    """세션 끝에 한 번: 바뀐 페이지를 찾아 그래프를 맞추고 글을 검사한다."""
    sys.stdin.read()          # 파이프를 비운다. 안 읽으면 호출한 쪽이 깨진 파이프를 본다
    root = wiki_root()
    if not root.is_dir():
        return 0

    graph = root / ".graph" / "graph.json"
    try:
        marker = graph.stat().st_mtime
    except OSError:
        marker = 0.0

    changed = []
    for page in wiki_pages(root):
        try:
            if page.stat().st_mtime > marker:
                changed.append(page)
        except OSError:
            continue
    if not changed:
        return 0

    lines: list[str] = []
    if BUILDER.is_file():
        built = run([sys.executable, str(BUILDER), "--root", str(root)])
        if built:
            lines.append(built.splitlines()[0])

    if CHECKER.is_file() and len(changed) <= MAX_PAGES:
        found = run([sys.executable, str(CHECKER), "--exit-zero", "--limit", LIMIT]
                    + [str(page) for page in changed])
        # 마지막 줄은 집계다. 그 줄만 있으면 경고가 없다는 뜻이므로 싣지 않는다.
        if found and len(found.splitlines()) > 1:
            lines.append(found)

    if lines:
        print("wiki-sync: 이 세션에서 위키 페이지 %d개가 바뀌었다 "
              "(Write/Edit 이 아닌 경로로 바뀐 것도 포함)." % len(changed))
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
