#!/usr/bin/env python3
"""위키에서 질문과 관련된 페이지를 찾아 돌려준다.

    recall.py "질문" [--top 3] [--mode auto|cag|rag] [--full] [--format text|json]
    printf '문구1\n문구2\n' | recall.py --excerpt [--cwd 작업폴더]   # 깊게 찾기의 발췌 단계

두 가지 방식이 있고, 위키 크기로 고른다(--mode auto).

  CAG  위키가 작으면(기본 3만 자 이하) 페이지 전부를 관련 순으로 돌려준다. 찾다가 놓칠 일이
       없고, 그 정도 분량은 통째로 읽어도 된다
  RAG  위키가 크면 관련이 높은 몇 장만 돌려준다. 다 읽을 수 없으니 고른다

찾는 법:

  - 한국어는 띄어쓰기만으로 낱말이 나뉘지 않는다("검색실패", "검색 실패"). 그래서 두 글자씩
    겹쳐 자른 조각으로 비교한다. 형태소 분석기 없이 대부분의 경우를 맞춘다
  - 순위는 BM25 로 매긴다. 흔한 조각보다 드문 조각이 맞을 때 점수를 더 준다
  - 제목과 목차(index.md)의 한 줄 설명에 든 조각은 두 번 더 센다. 둘 다 페이지가 무엇에
    관한 것인지의 가장 짧은 요약이다
  - 질문 낱말에서 조사만 남은 덩어리("Tauri를" 의 '를')와 풀이말("뭐였지", "할까")은 뺀다.
    무엇을 묻는지는 말하지 않는데 위키에 없어서 무게만 커, 맞는 페이지의 덮는 비율을 깎는다
  - 질문을 덮는 비율은 페이지 전체가 아니라 덩어리(문단 하나, 표의 한 줄 하나)마다 재고 가장
    잘 덮는 덩어리로 정한다. 긴 페이지가 웬만한 낱말을 다 가져서 늘 붙던 것을 막는다
  - 작업 폴더(--cwd)를 주면 그 프로젝트의 주제, 메시지가 이름을 말한 주제, 공용 주제
    (--shared-topics)만 붙인다. 훅이 준다
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
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
HANGUL_RUN = re.compile(r"[가-힣]+")
LATIN_WORD = re.compile(r"[a-z0-9][a-z0-9_-]+")
TITLE_LINE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
# 목차 한 줄. llm-wiki-docs/scripts/_wiki.py 의 ENTRY 와 같은 모양이다(그쪽이 이 줄을 쓴다).
INDEX_ENTRY = re.compile(r"^- \[[^\]]+\]\((?P<file>[^)]+)\)\s*(?:—|-)?\s*(?P<summary>.*)$")
SKIP_NAMES = {"index.md", "log.md"}
# 한글 음절의 받침 번호를 셈하는 값. 유니코드는 음절을 0xAC00 + (초성×21 + 중성)×28 + 받침
# 으로 만든다(Unicode Standard 3.12 "Conjoining Jamo Behavior"). 받침 0 은 받침 없음이다.
HANGUL_FIRST = 0xAC00
FINALS_PER_SYLLABLE = 28
FINAL_SS = 20             # ㅆ
FINAL_L = 8               # ㄹ
# 이름씨 + '이었/였'("방식이었습니다", "주제였어"). 이름씨는 두 글자 이상만 — "뭐였지" 의 '뭐'
# 처럼 한 글자는 거의 다 묻는 말이다.
COPULA_PAST = re.compile(r"^(?P<noun>[가-힣]{2,}?)(?:이었|였)")
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


def query_words(query, stop_tokens, particles, wiki_text=""):
    """질문을 낱말로 나눈다. 한국어 낱말은 끝의 조사·어미를 뗀다.

    겹침을 조각 수로 세면 "플러그인" 한 낱말이 조각 셋(플러/러그/그인)이 되어, 낱말 하나만
    같아도 "충분히 겹친다" 가 된다. 낱말 수로 세야 기준이 뜻대로 움직인다.
    wiki_text 는 위키 글 전체(소문자)다. 떼고 한 글자만 남을 때 splits_off 가 견준다.
    """
    lowered = query.lower()
    words = set(LATIN_WORD.findall(lowered))
    for run in HANGUL_RUN.findall(lowered):
        # "Tauri를", "API가" 는 영문 뒤에 조사만 붙은 것이라 한글 덩어리 전체가 조사다.
        # 실제 메시지 1,163개에서 이런 덩어리가 낱말로 1,000번 넘게 셈해졌다(2026-11-20).
        if run in particles:
            continue
        for ending in sorted(particles, key=len, reverse=True):
            if run.endswith(ending) and len(run) > len(ending):
                if splits_off(run[:-len(ending)], ending, wiki_text):
                    run = run[:-len(ending)]
                break
        if is_predicate(run):
            # "주제였어" 는 풀이말이지만 앞의 이름씨 "주제" 는 무엇을 묻는지 말한다. 그것만 남긴다.
            noun = COPULA_PAST.match(run)
            if not noun or is_predicate(noun.group("noun")):
                continue
            run = noun.group("noun")
        words.add(run)
    filler = load_word_list("stop-words.txt")
    return {word for word in words if word not in stop_tokens and word not in filler}


def splits_off(stem, ending, wiki_text):
    """조사를 떼고 stem 만 남기는 게 맞는가.

    한 글자만 남을 때는 글자만 봐서 가를 수 없다. "훅이" 는 '훅'+조사지만 "결과·통과·추가" 는
    통째로 이름씨다. 그래서 위키가 더 많이 쓰는 꼴을 따른다: 통째("결과")로 나온 수와, 그 한
    글자가 홀로 서거나 다른 조사를 달고("앱을", "앱 ") 나온 수를 견준다. 위키 글이 없으면 뗀다.
    실제 메시지 1,163개의 두 글자 낱말을 손으로 갈라 재니(2026-11-20), 늘 떼면 통째 이름씨
    491번을 모두 잘랐고, 한 글자면 안 떼면 한 글자 이름씨 449번을 모두 놓쳤다. 이 규칙은
    각각 392번·440번을 맞혔다. 남는 틀림은 위키에 없는 드문 낱말('위도' → '위')이다.
    """
    if len(stem) > 1 or not wiki_text:
        return True
    endings = one_letter_endings(wiki_text).get(stem, {})
    other = sum(count for found, count in endings.items() if found != ending)
    return other >= wiki_text.count(stem + ending)


@functools.lru_cache(maxsize=1)
def one_letter_endings(wiki_text):
    """위키에서 홀로 선 한 글자 → 뒤에 붙은 조사별 수("" 는 조사 없음). 위키마다 한 번 센다."""
    endings = "|".join(re.escape(ending) for ending in
                       sorted(load_word_list("particles.txt"), key=len, reverse=True))
    pattern = re.compile(r"(?<![가-힣])([가-힣])(" + endings + r")?(?![가-힣])")
    found = collections.defaultdict(collections.Counter)
    for match in pattern.finditer(wiki_text):
        found[match.group(1)][match.group(2) or ""] += 1
    return found


def wiki_text_of(pages):
    """splits_off 가 견줄 위키 글 전체(소문자)."""
    return "\n".join((page["title"] + "\n" + page["summary"] + "\n" + page["body"]).lower()
                     for page in pages)


def is_predicate(word):
    """'뭐였지', '정했지', '할까' 같은 풀이말인가. 무엇을 묻는지가 아니라 어떻게 묻는지를 말한다.

    ㅆ 받침은 '했·였·있·겠' 처럼 풀이말에서만 나오고, 'ㄹ 받침 + 까'(할까·바꿀까)는 묻는
    끝말이다. 실제 메시지 1,163개와 위키에서 이 규칙에 걸린 523가지를 모두 읽었는데 전부
    풀이말이었다(2026-11-20). 이름씨에 '이었/였' 이 붙은 꼴은 query_words 가 이름씨만 남긴다.
    """
    if not HANGUL_RUN.fullmatch(word):
        return False
    finals = [(ord(letter) - HANGUL_FIRST) % FINALS_PER_SYLLABLE for letter in word]
    if FINAL_SS in finals:
        return True
    return len(word) >= 2 and word.endswith("까") and finals[-2] == FINAL_L


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


def index_summaries(wiki_dir):
    """목차(index.md)의 한 줄 설명. 페이지 경로 → 설명. 목차가 없으면 빈 사전이다.

    목차 줄은 사람이 "이 페이지에 무엇이 있나" 를 한 줄로 쓴 것이라, 본문에 없는 말("Tauri를
    고른 이유")이 들어 있다. 목차 파일 자체는 검색하지 않으므로, 설명을 그 페이지에 붙여 찾는다.
    """
    summaries = {}
    try:
        with open(os.path.join(wiki_dir, "index.md"), encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = INDEX_ENTRY.match(line.strip())
                if match and match.group("summary").strip():
                    path = os.path.normpath(os.path.join(wiki_dir, match.group("file")))
                    summaries[unicodedata.normalize("NFC", path)] = match.group("summary").strip()
    except OSError:
        return {}
    return summaries


def collect_pages(root):
    """<뿌리>/<토픽>/wiki/**.md 의 (경로, 제목, 목차 설명, 본문). 목차와 기록은 빼고 준다."""
    pages = []
    try:
        topic_names = sorted(os.listdir(root))
    except OSError:
        return pages
    for topic in topic_names:
        wiki_dir = os.path.join(root, topic, "wiki")
        if topic.startswith(".") or not os.path.isdir(wiki_dir):
            continue
        summaries = index_summaries(wiki_dir)
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
                # 맥의 파일 이름은 한글이 풀어 쓴 꼴(NFD)일 수 있어, 목차 쪽과 같은 꼴로 맞춰 찾는다.
                summary = summaries.get(unicodedata.normalize("NFC", os.path.normpath(path)), "")
                pages.append({"path": path, "title": title, "summary": summary, "body": body})
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


def chunks_of(body):
    """페이지를 덩어리로 나눈다: 문단 하나, 표의 한 줄 하나. 제목 줄과 빈 줄은 덩어리를 끊는다."""
    pieces, paragraph = [], []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "|")):
            paragraph.append(stripped)
            continue
        if paragraph:
            pieces.append(" ".join(paragraph))
            paragraph = []
        if stripped.startswith("|") and not stripped.startswith("|---"):
            pieces.append(stripped)
    if paragraph:
        pieces.append(" ".join(paragraph))
    return pieces or [""]


def best_chunk(page, words, weights, total_weight, stop_tokens):
    """질문을 가장 잘 덮는 덩어리의 (덮는 비율, 맞은 낱말 수).

    페이지 전체로 재면 긴 페이지가 웬만한 낱말을 다 가져서 늘 기준을 넘는다. 2026-11-20 실제
    메시지 1,163개 중 533개에 붙었고, 거의 다 결정 기록 한 장(7만 바이트)이었다 — "고마워, 오늘은
    여기까지 하자" 에도. 질문 낱말이 한 덩어리 안에 함께 있어야 그 덩어리가 질문에 관한 것이다.
    제목·목차 설명은 페이지 전체의 요약이라 모든 덩어리에 같이 친다.
    """
    head = page["title"] + "\n" + page["summary"]
    best = (0.0, 0)
    for chunk in chunks_of(page["body"]):
        text = chunk + "\n" + head
        token_set, lowered = set(tokens_of(text, stop_tokens)), text.lower()
        matched = [word for word in words if page_has_word(token_set, lowered, word)]
        best = max(best, (sum(weights[word] for word in matched) / total_weight, len(matched)))
    return best


def topic_of(path, root):
    """페이지가 든 주제 폴더 이름. <뿌리>/<주제>/wiki/... 의 <주제> 다."""
    return os.path.relpath(path, root).split(os.sep)[0]


def topic_allowed(topic, cwd, query, shared_topics):
    """지금 작업 폴더에서 이 주제의 페이지를 붙여도 되나.

    주제 이름이 작업 폴더 경로의 한 칸이면 같은 프로젝트다. 다른 프로젝트의 페이지는 낱말이
    맞아도 그 프로젝트 이야기가 아니다 — 2026-11-20 실제 메시지에서 문단 단위로 잰 뒤에도 붙은
    130개 중 70개가 다른 프로젝트 세션에 붙은 Capitis 페이지였다. 메시지가 주제 이름을 말하면
    그 주제를 묻는 것이니 허용하고, 어느 프로젝트에도 속하지 않는 주제(shared_topics)는 늘 허용한다.
    """
    topic = topic.lower()
    parts = {part.lower() for part in os.path.normpath(cwd).split(os.sep) if part}
    return topic in parts or topic in query.lower() or topic in shared_topics


def recall(query, options):
    """질문에 맞는 페이지 목록과 고른 방식(cag/rag)을 돌려준다."""
    stop_tokens = load_stop_tokens()
    root = wiki_root(options.root)
    pages = collect_pages(root)
    if not pages:
        return "none", [], 0
    query_tokens = tokens_of(query, stop_tokens)
    words = query_words(query, stop_tokens, load_word_list("particles.txt"), wiki_text_of(pages))
    # 제목·목차 설명 조각을 두 번 더 넣는 것으로 가중치를 준다. 따로 점수를 매기는 것보다 단순하다.
    page_tokens = [tokens_of(page["body"], stop_tokens)
                   + 2 * tokens_of(page["title"] + "\n" + page["summary"], stop_tokens)
                   for page in pages]
    scores = bm25_scores(query_tokens, page_tokens)
    total_chars = sum(len(page["body"]) for page in pages)
    mode = options.mode
    if mode == "auto":
        mode = "cag" if total_chars <= options.cag_max_chars else "rag"

    # 낱말마다 무게: 드문 낱말일수록 무겁다. 위키에 아예 없는 낱말이 가장 무겁다 — 질문이
    # 위키가 모르는 것을 묻고 있다는 뜻이고, 그러면 덮는 비율이 낮게 나와야 맞다.
    token_sets = [set(tokens) for tokens in page_tokens]
    bodies = [(page["body"] + "\n" + page["summary"]).lower() for page in pages]
    weights = {}
    for word in words:
        having = sum(1 for token_set, body in zip(token_sets, bodies)
                     if page_has_word(token_set, body, word))
        weights[word] = math.log(1 + (len(pages) - having + 0.5) / (having + 0.5))
    total_weight = sum(weights.values()) or 1.0

    hits = []
    for page, score in zip(pages, scores):
        coverage, shared = best_chunk(page, words, weights, total_weight, stop_tokens)
        hits.append(dict(page, score=score, shared=shared, coverage=coverage, via=None,
                         lines=best_lines(page["body"], query_tokens, stop_tokens)))
    hits.sort(key=lambda hit: -hit["score"])
    if options.cwd:
        shared_topics = shared_topic_set(options.shared_topics)
        hits = [hit for hit in hits
                if topic_allowed(topic_of(hit["path"], root), options.cwd, query, shared_topics)]

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
            # 더하기 전에 본다. 더한 뒤에 보면 다음 상위 페이지의 반복이 한 장을 더 붙인다.
            if len(chosen) >= options.top + 2:
                break
            if neighbour_path in taken or neighbour_path not in by_path:
                continue
            taken.add(neighbour_path)
            chosen.append(dict(by_path[neighbour_path], score=hit["score"] * NEIGHBOUR_WEIGHT,
                               via=hit["title"]))
    return mode, chosen, len(pages)


def shared_topic_set(text):
    """쉼표로 적은 공용 주제 → 소문자 이름 집합."""
    return {name.strip().lower() for name in text.split(",") if name.strip()}


def excerpts(phrases, options):
    """핵심 문구마다 그 낱말이 모두 든 덩어리를 모두 모은다. 깊게 찾기의 발췌 단계다.

    낱말을 합쳐 한 번 찾으면, 여러 가지를 한꺼번에 말한 메시지는 낱말이 여러 줄에 흩어져 어느
    덩어리도 기준을 못 넘는다. 문구마다 따로 찾으면 각 주제의 줄을 따로 잡는다 — 2026-11-20 표본
    36개에서 맞는 줄이 든 경우가 27개(합쳐 한 번 찾고 핵심 줄 2개)에서 33개로 늘었다.
    → (발췌 [(페이지, 덩어리, [문구…])], 흔해서 뺀 [(문구, 걸린 수)], 못 찾은 [문구])
    """
    stop_tokens = load_stop_tokens()
    particles = load_word_list("particles.txt")
    root = wiki_root(options.root)
    pages = collect_pages(root)
    every_chunk = [(page, chunk) for page in pages for chunk in chunks_of(page["body"])]
    shared_topics = shared_topic_set(options.shared_topics)
    asked = "\n".join(phrases)
    searchable = [(index, page, chunk, set(tokens_of(chunk, stop_tokens)), chunk.lower())
                  for index, (page, chunk) in enumerate(every_chunk)
                  if not options.cwd
                  or topic_allowed(topic_of(page["path"], root), options.cwd, asked, shared_topics)]
    common_limit = options.common_share * len(every_chunk)
    found, common, missing = {}, [], []
    wiki_text = wiki_text_of(pages)
    for phrase in phrases:
        words = query_words(phrase, stop_tokens, particles, wiki_text)
        matches = [entry for entry in searchable
                   if words and all(page_has_word(entry[3], entry[4], word) for word in words)]
        if not matches:
            missing.append(phrase)
        elif len(matches) > common_limit:
            common.append((phrase, len(matches)))
        else:
            for index, page, chunk, _, _ in matches:
                found.setdefault(index, (page, chunk, []))[2].append(phrase)
    # 페이지 순서, 페이지 안에서는 글 순서로 — 같은 페이지의 발췌가 흩어지지 않게
    return [found[index] for index in sorted(found)], common, missing


def render_excerpts(found, common, missing, phrase_count):
    """발췌를 페이지별로 묶어 글로. 모델이 읽고 질문에 맞게 정리할 재료다."""
    if not found:
        return ""
    pages = []
    for page, _, _ in found:
        if page["path"] not in pages:
            pages.append(page["path"])
    lines = ["wiki-recall 발췌: 문구 %d개 → 덩어리 %d개 (페이지 %d개)" % (phrase_count, len(found), len(pages))]
    if common:
        lines.append("흔해서 뺀 문구: " + ", ".join("%s(덩어리 %d개)" % pair for pair in common))
    if missing:
        lines.append("찾지 못한 문구: " + ", ".join(missing))
    current = None
    for page, chunk, matched in found:
        if page["path"] != current:
            current = page["path"]
            lines.append("\n== %s — %s" % (page["path"], page["title"]))
        lines.append("- [%s] %s" % (", ".join(matched), chunk))
    return "\n".join(lines)


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
    parser.add_argument("--cwd", default="",
                        help="지금 작업 폴더. 주면 이 프로젝트의 주제·이름을 말한 주제·공용 주제만 붙인다")
    parser.add_argument("--shared-topics", default=os.environ.get("WIKI_RECALL_SHARED_TOPICS", ""),
                        help="어느 프로젝트에도 속하지 않아 늘 붙여도 되는 주제, 쉼표로 (기본: "
                             "WIKI_RECALL_SHARED_TOPICS)")
    parser.add_argument("--full", action="store_true", help="고른 페이지의 본문 전체를 붙인다")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--excerpt", action="store_true",
                        help="발췌 모드: 질문 대신 핵심 문구를 한 줄에 하나씩 받아, 문구마다 그 낱말이 "
                             "모두 든 덩어리를 출처와 함께 모두 찍는다")
    # 2026-11-20 표본(위키 167덩어리)에서 15개(약 9%) 넘게 걸리는 문구('위키' 같은 말)를 빼도
    # 맞는 줄이 든 수는 33/36 그대로였고 양만 줄었다. 8개(약 5%)로 낮추면 26/36 으로 떨어졌다.
    # 위키 크기가 바뀌어도 같은 뜻이 되게 개수가 아니라 비율로 둔다. 위키가 커지면 다시 잰다.
    parser.add_argument("--common-share", type=float, default=0.09,
                        help="발췌 모드에서 위키 전체 덩어리의 이 비율보다 많이 걸리는 문구는 흔해서 뺀다 (기본 0.09)")
    options = parser.parse_args(argv)

    # 질문을 인자 대신 표준입력으로 받을 수 있게 한 것은 훅 때문이다. 사용자 메시지에는
    # 따옴표·줄바꿈이 섞여 있어서, 명령줄 인자로 넘기면 그 자리에서 깨진다.
    query = options.query if options.query is not None else sys.stdin.read()
    if options.excerpt:
        phrases = [line.strip() for line in query.splitlines() if line.strip()]
        found, common, missing = excerpts(phrases, options)
        text = render_excerpts(found, common, missing, len(phrases))
        if text:
            print(text)
        return 0 if text else 1
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
