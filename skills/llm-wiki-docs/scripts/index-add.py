#!/usr/bin/env python3
"""Add or update one page's line in a wiki index.

  index-add.py <topic> <page.md> <category> "one line summary"

Why a script: the index is the front door — a page missing from it is a page
nobody finds, which is the same as not having written it. Doing this by hand is
what gets skipped, and hand-editing also drifts the line format, after which
lint.py stops recognising the entry.

Re-running for the same page replaces its line rather than adding a second one,
and moves it if the category changed. Two lines for one page is worse than none:
you fix one and the other keeps lying.
"""
import argparse
import sys

import _wiki


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic")
    ap.add_argument("page", help="file name inside wiki/, e.g. pathway-gating.md")
    ap.add_argument("category", help="index section to file it under, e.g. Concepts")
    ap.add_argument("summary", nargs="?", default="", help="one line on what it holds")
    args = ap.parse_args()

    page = args.page if args.page.endswith(".md") else args.page + ".md"
    if page in ("index.md", "log.md"):
        raise SystemExit(f"error: {page} is machinery, not a page to index")

    lines, entries = _wiki.read_index(args.topic)
    if not (_wiki.wiki_dir(args.topic) / page).exists():
        print(f"warning: {page} does not exist yet — the index entry will dangle "
              f"until you write it", file=sys.stderr)

    new_line = _wiki.entry_line(page, args.summary)
    existing = next((e for e in entries if e["file"] == page), None)

    if existing and existing["category"] == args.category:
        if lines[existing["lineno"]] == new_line:
            print(f"unchanged: {page} already filed under '{args.category}' with that summary")
            return
        lines[existing["lineno"]] = new_line
        _write(args.topic, lines)
        print(f"updated:   {page} under '{args.category}'")
        return

    if existing:
        del lines[existing["lineno"]]

    _insert(lines, args.category, new_line)
    _write(args.topic, lines)
    if existing:
        print(f"moved:     {page} '{existing['category']}' -> '{args.category}'")
    else:
        print(f"added:     {page} under '{args.category}'")


def _insert(lines, category, new_line):
    """Put new_line at the end of `## category`, adding the section if needed."""
    start = None
    for i, line in enumerate(lines):
        h = _wiki.HEADING.match(line)
        if h and h.group("name") == category:
            start = i
            break

    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([f"## {category}", "", new_line])
        return

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if _wiki.HEADING.match(lines[i]):
            end = i
            break

    section = [s for s in lines[start + 1:end] if s.strip() != _wiki.PLACEHOLDER]
    while section and not section[-1].strip():
        section.pop()
    section.append(new_line)
    lines[start + 1:end] = section


def _normalize(lines):
    """One blank line after each heading, none trailing, and a placeholder in any
    section left with no entries. The index is read by people, so a section that
    looks empty but is not, or a stale leftover heading, costs more than these
    few lines do."""
    out, i = [], 0
    while i < len(lines) and not _wiki.HEADING.match(lines[i]):
        out.append(lines[i])
        i += 1

    while i < len(lines):
        heading = lines[i]
        i += 1
        body = []
        while i < len(lines) and not _wiki.HEADING.match(lines[i]):
            body.append(lines[i])
            i += 1
        body = [b for b in body if b.strip() and b.strip() != _wiki.PLACEHOLDER]
        if not body:
            body = [_wiki.PLACEHOLDER]
        if out and out[-1].strip():
            out.append("")
        out += [heading, ""] + body
    return out


def _write(topic, lines):
    text = "\n".join(_normalize(lines)).rstrip("\n") + "\n"
    _wiki.index_path(topic).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
