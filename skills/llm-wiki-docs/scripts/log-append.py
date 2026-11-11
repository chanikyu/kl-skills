#!/usr/bin/env python3
"""Append one entry to a wiki's log.md.

  log-append.py <topic> <ingest|query|lint> "<title>" [--pages a.md,b.md] [--source X] [--note "..."]

Why a script: the log is append-only and grep-able only if every entry uses the
same prefix. Written by hand the date format drifts and entries occasionally get
inserted in the middle, which quietly destroys the one property the file has —
that reading it top to bottom is the order things happened.

This never rewrites existing lines. It only adds to the bottom.
"""
import argparse
import datetime

import _wiki

OPERATIONS = ("ingest", "query", "lint")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic")
    ap.add_argument("operation", choices=OPERATIONS,
                    help="which of the three wiki operations this was")
    ap.add_argument("title")
    ap.add_argument("--pages", default="",
                    help="comma-separated pages touched, e.g. a.md,b.md,index.md")
    ap.add_argument("--source", default="", help="raw/<file> or a URL")
    ap.add_argument("--note", default="",
                    help="what changed in the understanding — not just which files moved")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    day = args.date or datetime.date.today().isoformat()
    path = _wiki.log_path(args.topic)
    if not path.exists():
        raise SystemExit(f"error: {path} is missing — run new-topic.sh {args.topic} to refill it")

    block = [f"## [{day}] {args.operation} | {args.title}"]
    if args.source:
        block.append(f"- source: {args.source}")
    pages = [p.strip() for p in args.pages.split(",") if p.strip()]
    if pages:
        block.append(f"- pages touched: {', '.join(pages)}")
    if args.note:
        block.append(f"- note: {args.note}")

    existing = path.read_text(encoding="utf-8").rstrip("\n")
    path.write_text(existing + "\n\n" + "\n".join(block) + "\n", encoding="utf-8")
    print(f"appended to {path}:")
    print("  " + "\n  ".join(block))


if __name__ == "__main__":
    main()
