#!/usr/bin/env python3
"""위키에서 질문과 관련된 페이지를 찾아 돌려준다.

    recall.py "질문" [--top 3] [--mode auto|cag|rag] [--full] [--format text|json]

두 가지 방식이 있고, 위키 크기로 고른다(--mode auto).

  CAG  위키가 작으면(기본 3만 자 이하) 페이지 전부를 관련 순으로 돌려준다. 찾다가 놓칠 일이
       없고, 그 정도 분량은 통째로 읽어도 된다
  RAG  위키가 크면 관련이 높은 몇 장만 돌려준다. 다 읽을 수 없으니 고른다

찾는 법:

  - 한국어는 띄어쓰기만으로 낱말이 나뉘지 않는다("검색실패", "검색 실패"). 그래서 두 글자씩
    겹쳐 자른 조각으로 비교한다. 형태소 분석기 없이 대부분의 경우를 맞춘다
  - 순위는 BM25 로 매긴다. 흔한 조각보다 드문 조각이 맞을 때 점수를 더 준다
  - 제목에 든 조각은 두 번 더 센다. 제목은 페이지가 무엇에 관한 것인지의 가장 짧은 요약이다
  - 그래프(.graph/graph.json)가 있으면, 상위 페이지가 링크로 잇는 이웃도 낮은 점수로 붙인다.
    답이 바로 옆 페이지에 있는 경우가 많다

외부 패키지를 쓰지 않는다. 이 스크립트는 사용자가 말할 때마다 훅에서 돈다 — 설치 문제로
안 돌면 조용히 빠지는 것보다, 처음부터 의존할 것이 없는 쪽이 낫다.
"""

import argparse
import collections
import functools
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
HANGUL_RUN = re.compile(r"[가-힣]+")
LATIN_WORD = re.compile(r"[a-z0-9][a-z0-9_-]+")
TITLE_LINE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
SKIP_NAMES = {"index.md", "log.md"}
# BM25 의 표준 매개변수(Robertson & Zaragoza, 2009). k1 은 같은 조각이 반복될 때 점수가
# 얼마나 빨리 포화되는지, b 는 긴 페이지에 얼마나 벌점을 주는지 정한다.
BM25_K1 = 1.5
BM25_B = 0.75
NEIGHBOUR_WEIGHT = 0.3    # 링크로 따라온 이웃은 직접 맞은 페이지보다 낮게 친다


def load_word_list(filename):
    """data/ 의 낱말 목록 한 장. 파일이 없으면 빈 집합이다."""
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, encoding="utf-8") as handle:
            return {line.strip() for line in handle
                    if line.strip() and not line.startswith("#")}
    except OSError:
        return set()


def load_stop_tokens():
    """검색에서 뺄 조각."""
    return load_word_list("stop-tokens.txt")


def query_words(query, stop_tokens, particles):
    """질문을 낱말로 나눈다. 한국어 낱말은 끝의 조사·어미를 뗀다.

    겹침을 조각 수로 세면 "플러그인" 한 낱말이 조각 셋(플러/러그/그인)이 되어, 낱말 하나만
    같아도 "충분히 겹친다" 가 된다. 낱말 수로 세야 기준이 뜻대로 움직인다.
    """
    lowered = query.lower()
    words = set(LATIN_WORD.findall(lowered))
    for run in HANGUL_RUN.findall(lowered):
        for ending in sorted(particles, key=len, reverse=True):
            # 한 글자라도 남으면 뗀다. "훅이" 의 "훅" 처럼 한 글자 낱말이 주제인 경우가 있다.
            if run.endswith(ending) and len(run) > len(ending):
                run = run[:-len(ending)]
                break
        words.add(run)
    filler = load_word_list("stop-words.txt")
    return {word for word in words if word not in stop_tokens and word not in filler}


@functools.lru_cache(maxsize=None)
def standalone_letter(letter):
    """한 글자 낱말이 홀로 선 자리만 찾는 정규식. 뒤에 조사가 붙는 것까지는 같은 낱말로 본다.

    글에서 그냥 찾으면 '손' 이 "뇌 손상" 에서, '위' 가 "무작위" 에서 걸린다. 그런 글자는 다른
    페이지에 드물어서 무게가 커지고, 관련 없는 페이지가 "질문을 60% 덮음" 으로 붙었다
    (2026-11-11, hook-replay 로 세션 전체에서 3번 재현).
    """
    endings = "|".join(re.escape(ending) for ending in
                       sorted(load_word_list("particles.txt"), key=len, reverse=True))
    return re.compile(r"(?<![가-힣])" + re.escape(letter) + r"(?:" + endings + r")?(?![가-힣])")


def page_has_word(token_set, lowered_body, word):
    """페이지에 그 낱말이 있는가. 한국어 한 글자는 조각으로 못 맞추므로 글에서 홀로 선 자리를 찾는다."""
    if not HANGUL_RUN.fullmatch(word):
        return word in token_set
    if len(word) == 1:
        return bool(standalone_letter(word).search(lowered_body))
    return all(word[index:index + 2] in token_set for index in range(len(word) - 1))


def tokens_of(text, stop_tokens):
    """글을 비교용 조각 목록으로. 영문은 낱말, 한국어는 두 글자씩 겹쳐 자른 조각이다."""
    lowered = text.lower()
    pieces = LATIN_WORD.findall(lowered)
    for run in HANGUL_RUN.findall(lowered):
        if len(run) == 1:
            pieces.append(run)
        else:
            pieces.extend(run[index:index + 2] for index in range(len(run) - 1))
    return [piece for piece in pieces if piece not in stop_tokens]


def wiki_root(option_root):
    """위키 뿌리. 인자 → LLM_WIKI_ROOT → ~/llm-wiki-docs 순서로 정한다."""
    return os.path.abspath(os.path.expanduser(
        option_root or os.environ.get("LLM_WIKI_ROOT") or "~/llm-wiki-docs"))


def collect_pages(root):
    """<뿌리>/<토픽>/wiki/**.md 의 (경로, 제목, 본문). 목차와 기록은 빼고 준다."""
    pages = []
    try:
        topic_names = sorted(os.listdir(root))
    except OSError:
        return pages
    for topic in topic_names:
        wiki_dir = os.path.join(root, topic, "wiki")
        if topic.startswith(".") or not os.path.isdir(wiki_dir):
            continue
        for folder, subfolders, filenames in os.walk(wiki_dir):
            # 숨은 폴더(.git 등)는 위키 내용이 아니다. 그 안까지 들어가면 엉뚱한 글이 섞인다.
            subfolders[:] = [name for name in subfolders if not name.startswith(".")]
            for filename in sorted(filenames):
                if not filename.endswith(".md") or filename in SKIP_NAMES:
                    continue
                path = os.path.join(folder, filename)
                try:
                    with open(path, encoding="utf-8", errors="replace") as handle:
                        body = handle.read()
                except OSError:
                    continue
                title_match = TITLE_LINE.search(body)
                title = title_match.group(1) if title_match else filename[:-3]
                pages.append({"path": path, "title": title, "body": body})
    return pages


def bm25_scores(query_tokens, page_tokens):
    """페이지마다 BM25 점수. 질문에 든 조각이 드물고, 페이지에 자주 나올수록 높다."""
    page_count = len(page_tokens)
    if not page_count:
        return []
    average_length = sum(len(tokens) for tokens in page_tokens) / page_count or 1.0
    pages_having = collections.Counter(term for tokens in page_tokens for term in set(tokens))
    wanted = set(query_tokens)
    scores = []
    for tokens in page_tokens:
        counts = collections.Counter(tokens)
        score = 0.0
        for term in wanted:
            if term not in counts:
                continue
            # 드문 조각일수록 크다. 모든 페이지에 있는 조각은 0 에 가깝다.
            rarity = math.log(1 + (page_count - pages_having[term] + 0.5)
                              / (pages_having[term] + 0.5))
            frequency = counts[term]
            length_ratio = len(tokens) / average_length
            score += rarity * frequency * (BM25_K1 + 1) / (
                frequency + BM25_K1 * (1 - BM25_B + BM25_B * length_ratio))
        scores.append(score)
    return scores


def best_lines(body, query_tokens, stop_tokens, limit=2):
    """페이지에서 질문 조각이 가장 많이 든 줄 몇 개. 제목 줄과 빈 줄은 뺀다."""
    wanted = set(query_tokens)
    ranked = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|---"):
            continue
        shared = len(wanted & set(tokens_of(stripped, stop_tokens)))
        if shared:
            ranked.append((shared, stripped[:140]))
    ranked.sort(key=lambda pair: -pair[0])
    return [line for _, line in ranked[:limit]]


def graph_neighbours(root):
    """그래프 db 에서 경로 → 이웃 경로 목록. 그래프가 없으면 빈 사전이다."""
    graph_path = os.path.join(root, ".graph", "graph.json")
    try:
        with open(graph_path, encoding="utf-8") as handle:
            graph = json.load(handle)
    except (OSError, ValueError):
        return {}
    path_of = {node["id"]: node.get("path") for node in graph.get("nodes", [])
               if node.get("exists") and node.get("path")}
    neighbours = collections.defaultdict(set)
    for link in graph.get("links", []):
        source, target = path_of.get(link.get("source")), path_of.get(link.get("target"))
        if source and target:
            neighbours[source].add(target)
            neighbours[target].add(source)
    return neighbours


def recall(query, options):
    """질문에 맞는 페이지 목록과 고른 방식(cag/rag)을 돌려준다."""
    stop_tokens = load_stop_tokens()
    root = wiki_root(options.root)
    pages = collect_pages(root)
    if not pages:
        return "none", [], 0
    query_tokens = tokens_of(query, stop_tokens)
    words = query_words(query, stop_tokens, load_word_list("particles.txt"))
    # 제목 조각을 두 번 더 넣는 것으로 제목 가중치를 준다. 따로 점수를 매기는 것보다 단순하다.
    page_tokens = [tokens_of(page["body"], stop_tokens) + 2 * tokens_of(page["title"], stop_tokens)
                   for page in pages]
    scores = bm25_scores(query_tokens, page_tokens)
    total_chars = sum(len(page["body"]) for page in pages)
    mode = options.mode
    if mode == "auto":
        mode = "cag" if total_chars <= options.cag_max_chars else "rag"

    # 낱말마다 무게: 드문 낱말일수록 무겁다. 위키에 아예 없는 낱말이 가장 무겁다 — 질문이
    # 위키가 모르는 것을 묻고 있다는 뜻이고, 그러면 덮는 비율이 낮게 나와야 맞다.
    token_sets = [set(tokens) for tokens in page_tokens]
    bodies = [page["body"].lower() for page in pages]
    weights = {}
    for word in words:
        having = sum(1 for token_set, body in zip(token_sets, bodies)
                     if page_has_word(token_set, body, word))
        weights[word] = math.log(1 + (len(pages) - having + 0.5) / (having + 0.5))
    total_weight = sum(weights.values()) or 1.0

    hits = []
    for page, token_set, lowered_body, score in zip(pages, token_sets, bodies, scores):
        matched = [word for word in words if page_has_word(token_set, lowered_body, word)]
        shared = len(matched)
        coverage = sum(weights[word] for word in matched) / total_weight
        hits.append(dict(page, score=score, shared=shared, coverage=coverage, via=None,
                         lines=best_lines(page["body"], query_tokens, stop_tokens)))
    hits.sort(key=lambda hit: -hit["score"])

    if mode == "cag":
        return mode, hits, len(pages)

    # RAG: 질문과 조각을 충분히 나눈 페이지만, 위에서부터 몇 장.
    chosen = [hit for hit in hits if hit["shared"] >= options.min_shared
              and hit["coverage"] >= options.min_coverage][:options.top]
    taken = {hit["path"] for hit in chosen}
    neighbours = graph_neighbours(root)
    by_path = {hit["path"]: hit for hit in hits}
    for hit in list(chosen[:2]):
        for neighbour_path in sorted(neighbours.get(hit["path"], ())):
            if neighbour_path in taken or neighbour_path not in by_path:
                continue
            taken.add(neighbour_path)
            chosen.append(dict(by_path[neighbour_path], score=hit["score"] * NEIGHBOUR_WEIGHT,
                               via=hit["title"]))
            if len(chosen) >= options.top + 2:
                break
    return mode, chosen, len(pages)


def render_text(mode, hits, page_count, options):
    """찾은 것을 사람과 모델이 읽을 글로 만든다."""
    if not hits:
        return ""
    header = {"cag": "wiki-recall: 위키가 작아 전부 가져왔다 (CAG) — 페이지 %d개, 관련 순",
              "rag": "wiki-recall: 관련 페이지를 골랐다 (RAG) — 페이지 %d개 중 %d개"}[mode]
    lines = [header % ((page_count,) if mode == "cag" else (page_count, len(hits)))]
    for hit in hits:
        origin = " — %s 에서 링크로 이어진 페이지" % hit["via"] if hit["via"] else ""
        lines.append("- %s — %s (점수 %.1f, 질문을 %d%% 덮음%s)"
                     % (hit["path"], hit["title"], hit["score"], 100 * hit["coverage"], origin))
        lines.extend("    " + line for line in hit["lines"])
    if options.full:
        for hit in hits:
            lines.append("\n===== %s =====\n%s" % (hit["path"], hit["body"].rstrip()))
    return "\n".join(lines)


def main(argv=None):
    """명령줄 입구. 찾은 것이 없으면 아무것도 찍지 않고 1로 끝낸다."""
    parser = argparse.ArgumentParser(description="위키에서 질문과 관련된 페이지를 찾는다.")
    parser.add_argument("query", nargs="?", default=None, help="없으면 표준입력에서 읽는다")
    parser.add_argument("--root", default=None)
    parser.add_argument("--top", type=int, default=3, help="RAG 에서 고를 페이지 수 (기본 3)")
    parser.add_argument("--mode", choices=("auto", "cag", "rag"), default="auto")
    parser.add_argument("--cag-max-chars", type=int, default=30000,
                        help="위키 전체가 이 글자 수 이하면 auto 가 CAG 를 고른다 (기본 3만)")
    parser.add_argument("--min-shared", type=int, default=2,
                        help="RAG 에서 질문의 낱말을 이만큼 가진 페이지만 고른다 (기본 2)")
    parser.add_argument("--min-coverage", type=float, default=0.0,
                        help="RAG 에서 질문을 이 비율 이상 덮는 페이지만 고른다 (0~1, 기본 0)")
    parser.add_argument("--full", action="store_true", help="고른 페이지의 본문 전체를 붙인다")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    options = parser.parse_args(argv)

    # 질문을 인자 대신 표준입력으로 받을 수 있게 한 것은 훅 때문이다. 사용자 메시지에는
    # 따옴표·줄바꿈이 섞여 있어서, 명령줄 인자로 넘기면 그 자리에서 깨진다.
    query = options.query if options.query is not None else sys.stdin.read()
    mode, hits, page_count = recall(query, options)
    if options.format == "json":
        print(json.dumps({"mode": mode, "pages": page_count,
                          "hits": [{key: hit[key] for key in ("path", "title", "score", "coverage", "via", "lines")}
                                   for hit in hits]}, ensure_ascii=False, indent=1))
        return 0 if hits else 1
    text = render_text(mode, hits, page_count, options)
    if text:
        print(text)
    return 0 if text else 1


if __name__ == "__main__":
    sys.exit(main())
