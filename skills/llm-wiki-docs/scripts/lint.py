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
import sys

import _wiki

CHECKS = ("not-indexed", "not-logged", "dangling-index", "duplicate-index",
          "broken-link", "orphan")
# The entry point is meant to be reached from the index, so it is never an orphan.
ORPHAN_EXEMPT = {"overview.md"}


def lint(topic):
    findings = {k: [] for k in CHECKS}
    page_files = [p.name for p in _wiki.pages(topic)]
    _, entries = _wiki.read_index(topic)
    indexed = [e["file"] for e in entries]

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
    for page in _wiki.pages(topic):
        text = page.read_text(encoding="utf-8")
        for target in _wiki.wikilink_targets(text):
            if target not in page_files:
                findings["broken-link"].append(f"{page.name} -> [[{target[:-3]}]]")
            elif target != page.name:          # a page linking to itself proves nothing
                linked_to.add(target)

    for name in page_files:
        if name not in linked_to and name not in ORPHAN_EXEMPT:
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
