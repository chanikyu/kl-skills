"""Shared bits for the llm-wiki-docs scripts: where the wiki is, and how to
read index.md and the pages.

Kept in one place so index-add, log-append and lint cannot disagree about the
entry format — if they did, one would quietly stop seeing the other's work.
"""
import os
import pathlib
import re

# `- [label](file.md) — summary`  (an em dash, or a plain hyphen, separates them)
ENTRY = re.compile(r"^- \[(?P<label>[^\]]+)\]\((?P<file>[^)]+)\)\s*(?:—|-)?\s*(?P<summary>.*)$")
HEADING = re.compile(r"^## +(?P<name>.+?)\s*$")
WIKILINK = re.compile(r"\[\[(?P<target>[^\]|#]+)(?:[|#][^\]]*)?\]\]")
PLACEHOLDER = "_(nothing yet)_"


def root() -> pathlib.Path:
    """Where all wikis live. Never hardcoded, so another machine can differ."""
    return pathlib.Path(os.environ.get("LLM_WIKI_ROOT") or
                        (pathlib.Path.home() / "llm-wiki-docs")).expanduser()


def topic_dir(topic: str) -> pathlib.Path:
    if not topic or "/" in topic or topic.startswith("-") or topic in (".", ".."):
        raise SystemExit(f"error: topic must be a single name, not a path: {topic!r}")
    d = root() / topic
    if not (d / "wiki").is_dir():
        raise SystemExit(
            f"error: no wiki at {d}/wiki\n"
            f"       create it first:  new-topic.sh {topic}"
        )
    return d


def wiki_dir(topic: str) -> pathlib.Path:
    return topic_dir(topic) / "wiki"


def index_path(topic: str) -> pathlib.Path:
    return wiki_dir(topic) / "index.md"


def log_path(topic: str) -> pathlib.Path:
    return wiki_dir(topic) / "log.md"


def pages(topic: str):
    """Every page in the wiki — index.md and log.md are machinery, not pages."""
    return sorted(p for p in wiki_dir(topic).glob("*.md")
                  if p.name not in ("index.md", "log.md"))


def read_index(topic: str):
    """-> (lines, entries). Each entry: dict(category, file, label, summary, lineno)."""
    path = index_path(topic)
    if not path.exists():
        raise SystemExit(f"error: {path} is missing — run new-topic.sh {topic} to refill it")
    lines = path.read_text(encoding="utf-8").splitlines()
    entries, category = [], None
    for i, line in enumerate(lines):
        h = HEADING.match(line)
        if h:
            category = h.group("name")
            continue
        m = ENTRY.match(line)
        if m:
            entries.append({
                "category": category,
                "file": m.group("file"),
                "label": m.group("label"),
                "summary": m.group("summary").strip(),
                "lineno": i,
            })
    return lines, entries


def entry_line(page_file: str, summary: str) -> str:
    label = page_file[:-3] if page_file.endswith(".md") else page_file
    return f"- [{label}]({page_file}) — {summary}" if summary else f"- [{label}]({page_file})"


def wikilink_targets(text: str):
    """Link targets as page filenames, so they can be compared against pages()."""
    out = []
    for m in WIKILINK.finditer(text):
        t = m.group("target").strip()
        out.append(t if t.endswith(".md") else f"{t}.md")
    return out
