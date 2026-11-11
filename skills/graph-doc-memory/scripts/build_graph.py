#!/usr/bin/env python3
"""Compile every llm-wiki page under one root into a single graph.

    build_graph.py [--root DIR] [--out DIR] [--quiet]

Writes two files into <out> (default <root>/.graph):

    graph.json   the database. nodes + links + per-node degrees and stats.
    graph.html   the viewer, with graph.json inlined into it.

The data is inlined into the viewer on purpose. A browser opening a file:// page
cannot fetch() a sibling .json — same-origin rules treat every local file as a
different origin — so a viewer that loaded the json separately would need a local
web server, a port, and a background process to shut down. Inlining removes all
three. graph.json stays the one hand-readable, greppable copy; graph.html is a
build artifact that is overwritten on every run and never edited by hand.

Scope: only <root>/<topic>/wiki/**/*.md becomes a node. raw/ is sources, and the
topic README.md is the schema doc, not knowledge — neither belongs in the graph.

Root resolution, so nothing is pinned to one machine:
    --root  ->  $LLM_WIKI_ROOT  ->  ~/llm-wiki-docs
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import unquote

# Written as `[[page]]`, `[[page|alias]]`, `[[page#heading]]`, `[[sub/page]]`.
WIKILINK = re.compile(r"\[\[([^\[\]\n]+?)\]\]")
# Written as `[text](page.md)`. index.md uses this form.
MDLINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")
# Fenced blocks and inline code hold examples, not real links to this wiki.
FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def strip_code(text):
    return INLINE_CODE.sub(" ", FENCE.sub("\n", text))


def page_id(topic, rel):
    """`<topic>/<path-without-.md>` — unique across the whole root."""
    return "%s/%s" % (topic, rel[:-3] if rel.endswith(".md") else rel)


def find_topics(root):
    """A topic is a direct subdirectory that has a wiki/ inside it."""
    out = []
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return out
    for name in names:
        if name.startswith("."):
            continue
        if os.path.isdir(os.path.join(root, name, "wiki")):
            out.append(name)
    return out


def collect_pages(root, topics):
    pages = {}
    for topic in topics:
        wiki = os.path.join(root, topic, "wiki")
        for dirpath, dirnames, filenames in os.walk(wiki):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in sorted(filenames):
                if not fn.endswith(".md") or fn.startswith("."):
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, wiki)
                try:
                    text = open(path, encoding="utf-8", errors="replace").read()
                    st = os.stat(path)
                except OSError:
                    continue
                title = H1.search(text)
                pages[page_id(topic, rel)] = {
                    "topic": topic,
                    "rel": rel,
                    "path": path,
                    "title": title.group(1).strip() if title else os.path.basename(rel)[:-3],
                    "bytes": st.st_size,
                    "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc)
                    .astimezone()
                    .strftime("%Y-%m-%d"),
                    "text": strip_code(text),
                }
    return pages


def raw_targets(text):
    """Every link target written on the page, before resolution."""
    out = []
    for m in WIKILINK.finditer(text):
        out.append(m.group(1).split("|")[0].split("#")[0])
    for m in MDLINK.finditer(text):
        t = unquote(m.group(1))
        if "://" in t or t.startswith(("#", "mailto:")):
            continue
        t = t.split("#")[0]
        # A relative link into the wiki is either a .md page or an extensionless name.
        if t.endswith(".md") or "." not in os.path.basename(t):
            out.append(t)
    return out


def resolve(target, topic, pages, by_name):
    """Turn a written link into a node id. Returns (id, exists)."""
    t = target.strip().strip("<>").replace("\\", "/")
    while t.startswith("./"):
        t = t[2:]
    t = t.lstrip("/")
    if t.endswith(".md"):
        t = t[:-3]
    if not t:
        return None, False

    # Same topic (also covers wiki/ subdirectories), then a full `<topic>/<page>`.
    for cand in ("%s/%s" % (topic, t), t):
        if cand in pages:
            return cand, True

    # A bare name that exists in exactly one other topic: cross-topic link.
    hits = by_name.get(os.path.basename(t).lower(), [])
    if len(hits) == 1:
        return hits[0], True

    # Nothing matched: a link to a page not written yet. Obsidian shows these too —
    # they are the gaps worth filling, so they stay in the graph, marked missing.
    return "%s/%s" % (topic, t), False


def build(root, out_dir, viewer_src):
    topics = find_topics(root)
    pages = collect_pages(root, topics)

    by_name = {}
    for pid, p in pages.items():
        by_name.setdefault(os.path.basename(p["rel"])[:-3].lower(), []).append(pid)

    nodes = {}
    for pid, p in pages.items():
        nodes[pid] = {
            "id": pid,
            "label": os.path.basename(p["rel"])[:-3],
            "title": p["title"],
            "topic": p["topic"],
            "path": p["path"],
            "exists": True,
            "bytes": p["bytes"],
            "mtime": p["mtime"],
            "in": 0,
            "out": 0,
        }

    seen = set()
    links = []
    for pid, p in sorted(pages.items()):
        for target in raw_targets(p["text"]):
            tid, exists = resolve(target, p["topic"], pages, by_name)
            if not tid or tid == pid:
                continue
            if not exists and tid not in nodes:
                nodes[tid] = {
                    "id": tid,
                    "label": os.path.basename(tid),
                    "title": os.path.basename(tid),
                    "topic": p["topic"],
                    "path": "",
                    "exists": False,
                    "bytes": 0,
                    "mtime": "",
                    "in": 0,
                    "out": 0,
                }
            key = (pid, tid)
            if key in seen:
                continue
            seen.add(key)
            links.append({"source": pid, "target": tid})
            nodes[pid]["out"] += 1
            nodes[tid]["in"] += 1

    node_list = [nodes[k] for k in sorted(nodes)]
    graph = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": root,
        "topics": topics,
        "stats": {
            "topics": len(topics),
            "pages": len(pages),
            "nodes": len(node_list),
            "links": len(links),
            "missing": sum(1 for n in node_list if not n["exists"]),
            "orphans": sum(1 for n in node_list if n["in"] == 0 and n["out"] == 0),
        },
        "nodes": node_list,
        "links": links,
    }

    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "graph.json")
    html_path = os.path.join(out_dir, "graph.html")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=1)
        f.write("\n")

    viewer = open(viewer_src, encoding="utf-8").read()
    # `</script` inside the payload would close the host tag early.
    payload = json.dumps(graph, ensure_ascii=False).replace("</", "<\\/")
    if "__GRAPH_DATA__" not in viewer:
        print("error: viewer template has no __GRAPH_DATA__ placeholder", file=sys.stderr)
        return graph, json_path, html_path, 1
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(viewer.replace("__GRAPH_DATA__", payload))

    return graph, json_path, html_path, 0


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Build the llm-wiki graph database.")
    ap.add_argument("--root", default=os.environ.get("LLM_WIKI_ROOT") or
                    os.path.join(os.path.expanduser("~"), "llm-wiki-docs"))
    ap.add_argument("--out", default=None, help="default: <root>/.graph")
    ap.add_argument("--viewer", default=os.path.join(here, "..", "assets", "viewer.html"))
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    root = os.path.abspath(os.path.expanduser(a.root))
    out_dir = os.path.abspath(os.path.expanduser(a.out)) if a.out else os.path.join(root, ".graph")

    if not os.path.isdir(root):
        print("no wiki root at %s — nothing to graph" % root, file=sys.stderr)
        return 0

    t0 = time.time()
    graph, json_path, html_path, rc = build(root, out_dir, os.path.abspath(a.viewer))
    if rc:
        return rc
    if not a.quiet:
        s = graph["stats"]
        print("graph built in %dms: %d topics, %d pages, %d links, %d missing, %d orphans"
              % ((time.time() - t0) * 1000, s["topics"], s["pages"], s["links"],
                 s["missing"], s["orphans"]))
        print("  db:     %s" % json_path)
        print("  viewer: %s" % html_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
