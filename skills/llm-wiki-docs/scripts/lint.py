#!/usr/bin/env python3
"""Find the mechanical inconsistencies in a wiki.

  lint.py [topic ...]        # no topic = every topic under the root

Reports six things, all of them pure comparisons between the files, the index
and the log, so the answer is the same every run. A human eyeballing this gets a
different answer each time, which is why it is a script:

  not-indexed      a page exists but index.md does not list it -> nobody finds it
  not-logged       a page exists but log.md never mentions it  -> the history lost it
  dangling-index   index.md lists a page that is not there     -> a dead link
  duplicate-index  one page listed twice                       -> fix one, the other lies
  broken-link      [[link]] to a page that does not exist      -> may be a gap, may be a typo
  orphan           no other page links to it                   -> reachable only via the index

broken-link is not always a defect: a link to a not-yet-written page is a
deliberate marker for a gap worth filling. It is listed so you can tell the two
apart, not so you can delete the links.

Exit code is 1 when anything was found, so it can gate a commit. Judgement calls
(stale claims, contradictions) are not here — those need reading, not comparing.
"""
import argparse
import posixpath
import sys

import _wiki

CHECKS = ("not-indexed", "not-logged", "dangling-index", "duplicate-index",
          "broken-link", "orphan")
# The entry point is meant to be reached from the index, so it is never an orphan.
ORPHAN_EXEMPT = {"overview.md"}
# Pages filed under this index section are entry points too (a hierarchical wiki's
# root page, say Wiki.md). The index template opens with this section.
ENTRY_CATEGORY = "Overview"


def resolver(page_files):
    """[[link]] -> page path under wiki/, the same way build_graph.py resolves it
    within a topic: the path itself first, then a bare name that exactly one page
    has. Two pages with one name is ambiguous, so the link counts as broken."""
    # Bare names are compared lowercased, as build_graph.py does, so the graph and the
    # lint never disagree about whether a link lands.
    by_name = {}
    for ref in page_files:
        by_name.setdefault(posixpath.basename(ref).lower(), []).append(ref)

    def resolve(target):
        """One link target -> the page path it points at, or None when no page
        (or more than one page) answers to it."""
        wanted = target.strip().replace("\\", "/")
        while wanted.startswith("./"):
            wanted = wanted[2:]
        wanted = wanted.lstrip("/")
        if wanted in page_files:
            return wanted
        hits = by_name.get(posixpath.basename(wanted).lower(), [])
        return hits[0] if len(hits) == 1 else None

    return resolve


def lint(topic):
    findings = {k: [] for k in CHECKS}
    wiki_pages = _wiki.pages(topic)
    page_files = [_wiki.page_ref(topic, path) for path in wiki_pages]
    resolve = resolver(page_files)
    _, entries = _wiki.read_index(topic)
    indexed = [e["file"] for e in entries]
    entry_points = ORPHAN_EXEMPT | {entry["file"] for entry in entries
                                    if entry["category"] == ENTRY_CATEGORY}

    for name in page_files:
        if name not in indexed:
            findings["not-indexed"].append(name)

    # The log is the only record of WHEN and WHY a page changed. A page the log never
    # mentions is a page whose history starts blank, and nothing else can reconstruct it.
    # Matching by filename is enough because log-append.py writes the filenames it touched.
    log = _wiki.log_path(topic)
    log_text = log.read_text(encoding="utf-8") if log.exists() else ""
    for name in page_files:
        if name not in log_text:
            findings["not-logged"].append(name)

    for name in indexed:
        if name not in page_files:
            findings["dangling-index"].append(name)

    for name in sorted(set(indexed)):
        if indexed.count(name) > 1:
            findings["duplicate-index"].append(f"{name} (x{indexed.count(name)})")

    linked_to = set()
    for page, ref in zip(wiki_pages, page_files):
        text = page.read_text(encoding="utf-8")
        for target in _wiki.wikilink_targets(text):
            found = resolve(target)
            if found is None:
                findings["broken-link"].append(f"{ref} -> [[{target[:-3]}]]")
            elif found != ref:                 # a page linking to itself proves nothing
                linked_to.add(found)

    for name in page_files:
        if name not in linked_to and name not in entry_points:
            findings["orphan"].append(name)

    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topics", nargs="*", help="default: every topic under the root")
    args = ap.parse_args()

    root = _wiki.root()
    topics = args.topics or sorted(
        d.name for d in root.iterdir() if (d / "wiki").is_dir()
    ) if root.is_dir() else []

    if not topics:
        print(f"no wikis under {root}")
        return 0

    total = 0
    for topic in topics:
        findings = lint(topic)
        count = sum(len(v) for v in findings.values())
        total += count
        head = f"{topic}: clean" if not count else f"{topic}: {count} finding(s)"
        print(head)
        for check in CHECKS:
            for item in findings[check]:
                print(f"  {check:<16} {item}")

    print(f"\n{total} finding(s) across {len(topics)} topic(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
