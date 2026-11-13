#!/usr/bin/env python3
"""Publish docs/wiki to the repository's GitHub Wiki tab.

docs/wiki is the source: tests check its links and its five languages, and changes to it are
reviewed with the code. The Wiki tab is a copy made by this script. Pages are copied one for
one, with three changes the Wiki tab needs:

  - a link to another wiki page drops ".md"            (Installation.md -> Installation)
  - a link or picture that leaves the wiki becomes a full GitHub address
      pictures -> https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>
      files    -> https://github.com/<owner>/<repo>/blob/<branch>/<path>
  - the footer each page repeats is dropped; the Wiki tab shows _Footer.md under every page

The repository address comes from `git remote get-url origin`, the branch from origin's HEAD.

  publish_wiki.py --out DIR     write the converted pages into DIR (no network; used by the test)
  publish_wiki.py --push        clone <repo>.wiki.git, replace its pages, commit and push
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI_SOURCE = os.path.join(REPO, "docs", "wiki")
FOOTER_PAGE = "_Footer.md"
PICTURE_EXTENSIONS = (".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp")
# 마크다운 링크 ](대상) 와 HTML 의 src="대상" / href="대상". 대상에 : 가 있으면(https: 등) 이미 바깥 주소다
LINK_TARGET = re.compile(r'(\]\(|(?:src|href)=")([^)"\s:]+)')


def git(*args):
    """저장소에서 git 을 돌려 출력(앞뒤 공백 제거)을 돌려준다."""
    return subprocess.run(["git", "-C", REPO] + list(args), check=True,
                          stdout=subprocess.PIPE, text=True).stdout.strip()


def repository_web_address():
    """origin 주소를 https://github.com/<owner>/<repo> 모양으로. ssh 주소도 받는다."""
    remote = git("remote", "get-url", "origin")
    remote = re.sub(r"^git@([^:]+):", r"https://\1/", remote)
    return re.sub(r"\.git$", "", remote)


def default_branch():
    """origin 의 기본 브랜치 이름. 알 수 없으면 지금 브랜치."""
    try:
        return git("symbolic-ref", "--short", "refs/remotes/origin/HEAD").split("/", 1)[1]
    except (subprocess.CalledProcessError, IndexError):
        return git("rev-parse", "--abbrev-ref", "HEAD")


def convert_target(target, page_names, web, raw_base, branch):
    """링크 대상 하나를 위키 탭에서 열리는 주소로 바꾼다. 바꿀 것이 없으면 그대로."""
    path, hash_mark, anchor = target.partition("#")
    if path.endswith(".md") and "/" not in path and path[:-3] in page_names:
        return path[:-3] + hash_mark + anchor
    if not path.startswith("../"):
        return target
    repo_path = os.path.normpath(os.path.join("docs", "wiki", path)).replace(os.sep, "/")
    if repo_path.lower().endswith(PICTURE_EXTENSIONS):
        return raw_base + repo_path
    return "%s/blob/%s/%s%s%s" % (web, branch, repo_path, hash_mark, anchor)


def without_footer(text, footer):
    """페이지 끝에 _Footer 와 같은 꼬리말이 --- 줄과 함께 있으면 뗀다(위키 탭이 _Footer 를 따로 붙인다)."""
    stripped = text.rstrip()
    if footer and stripped.endswith(footer):
        body = stripped[: -len(footer)].rstrip()
        if body.endswith("---"):
            return body[:-3].rstrip() + "\n"
    return text


def convert_pages(out_dir):
    """docs/wiki 의 모든 페이지를 바꿔 out_dir 에 쓴다. 쓴 페이지 이름 목록을 돌려준다."""
    web, branch = repository_web_address(), default_branch()
    owner_repo = web.split("github.com/", 1)[-1]
    raw_base = "https://raw.githubusercontent.com/%s/%s/" % (owner_repo, branch)
    names = sorted(name for name in os.listdir(WIKI_SOURCE) if name.endswith(".md"))
    page_names = {name[:-3] for name in names}
    with open(os.path.join(WIKI_SOURCE, FOOTER_PAGE), encoding="utf-8") as handle:
        footer = handle.read().strip()
    os.makedirs(out_dir, exist_ok=True)
    for name in names:
        with open(os.path.join(WIKI_SOURCE, name), encoding="utf-8") as handle:
            text = handle.read()
        # 꼬리말을 떼는 것은 링크를 바꾸기 전에 한다 — _Footer 원본과 글자가 같아야 알아본다
        if name != FOOTER_PAGE:
            text = without_footer(text, footer)
        text = LINK_TARGET.sub(lambda match: match.group(1) + convert_target(
            match.group(2), page_names, web, raw_base, branch), text)
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as handle:
            handle.write(text)
    return names


def push_to_wiki():
    """위키 저장소를 받아 페이지를 원본과 같게 바꾸고(없어진 페이지는 지운다) 커밋해 올린다."""
    wiki_remote = repository_web_address() + ".wiki.git"
    work = tempfile.mkdtemp(prefix="wiki-")
    try:
        subprocess.run(["git", "clone", "-q", wiki_remote, work], check=True)
        # 원본에 없는 페이지(웹에서 만든 첫 페이지 같은 것)가 남지 않게, 다 지우고 원본으로 다시 채운다
        for name in os.listdir(work):
            if name.endswith(".md"):
                os.remove(os.path.join(work, name))
        names = convert_pages(work)
        source_commit = git("rev-parse", "--short", "HEAD")
        subprocess.run(["git", "-C", work, "add", "-A"], check=True)
        if not subprocess.run(["git", "-C", work, "status", "--porcelain"], check=True,
                              stdout=subprocess.PIPE, text=True).stdout.strip():
            print("wiki: already up to date (%d pages)" % len(names))
            return 0
        subprocess.run(["git", "-C", work, "commit", "-q", "-m",
                        "Publish docs/wiki at %s" % source_commit], check=True)
        subprocess.run(["git", "-C", work, "push", "-q"], check=True)
        print("wiki: published %d pages from %s to %s" % (len(names), source_commit, wiki_remote))
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    """--out 이면 바꾼 페이지를 폴더에 쓰고, --push 면 위키 탭에 올린다."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", help="write the converted pages into this folder")
    mode.add_argument("--push", action="store_true", help="publish to <repo>.wiki.git")
    args = parser.parse_args()
    if args.push:
        return push_to_wiki()
    names = convert_pages(args.out)
    print("wiki: wrote %d pages to %s" % (len(names), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
