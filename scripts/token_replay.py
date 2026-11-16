#!/usr/bin/env python3
"""Estimate, from recorded Claude Code transcripts, how many tokens two changes would have saved.

Every request re-reads the conversation so far (cache reads: 98.4% of one long session's tokens,
measured 2026-11-16). This replays each transcript's per-request usage and asks:

  offload  — had bash-offload (hooks/py/bash-offload.py) been on, how many bytes of each long Bash
             result would have stayed out of the conversation, and how many later requests would
             have re-read them before the next compaction?
  cap K    — had auto-compaction fired whenever the context passed K tokens, what would each
             request have read? (sawtooth model: after a compaction the context restarts from the
             segment's own starting size; each extra compaction costs one read of K tokens)

It is an estimate, not a measurement: bytes become tokens at --bytes-per-token, and a request is
assumed to grow the same way it did in the real session. It says nothing about answer quality.
The offload thresholds are read from hooks/py/bash-offload.py so the two cannot drift apart.

  token_replay.py --days 30 --caps 250000,300000,400000 --out results/token-replay_30d.tsv
"""

import argparse
import glob
import importlib.util
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFLOAD_GATE = os.path.join(REPO, "hooks", "py", "bash-offload.py")
COMPACTION_DROP = 0.7          # 다음 요청의 문맥이 앞의 70% 아래로 떨어지면 압축(또는 정리)이 있었던 것으로 본다
NOTICE_BYTES = 160             # bash-offload 가 잘린 출력 사이에 넣는 안내 한 줄의 대략 크기


def offload_defaults():
    """bash-offload 게이트의 기본값(출력 상한·앞뒤 줄 수·줄 길이)을 그 파일에서 읽는다."""
    sys.path.insert(0, os.path.dirname(OFFLOAD_GATE))
    spec = importlib.util.spec_from_file_location("bash_offload", OFFLOAD_GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DEFAULTS


def kept_bytes(text, limits):
    """bash-offload 를 거쳤다면 대화에 남았을 바이트 수."""
    raw = text.encode("utf-8")
    if len(raw) <= limits["KL_OFFLOAD_MAX_BYTES"]:
        return len(raw)
    lines = text.splitlines()
    chars = limits["KL_OFFLOAD_LINE_CHARS"]
    kept = lines[:limits["KL_OFFLOAD_HEAD"]] + lines[-limits["KL_OFFLOAD_TAIL"]:]
    return sum(len(line[:chars].encode("utf-8")) + 1 for line in kept) + NOTICE_BYTES


def result_text(block):
    """tool_result 블록의 글(문자열이거나 글 조각 목록)."""
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def read_session(path):
    """요청별 문맥 크기와, 각 요청 직전에 들어온 Bash 결과의 (원래 바이트, 남을 바이트)를 순서대로."""
    requests, pending, bash_ids, seen = [], [], set(), set()
    # 한 응답이 여러 줄로 기록되므로 message.id 로 한 번만 센다. 하위 에이전트 줄(isSidechain)은 본 대화가 아니다
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict) or entry.get("isSidechain"):
                continue
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content") if isinstance(message.get("content"), list) else []
            if entry.get("type") == "assistant":
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Bash":
                        bash_ids.add(block.get("id"))
                usage = message.get("usage")
                if isinstance(usage, dict) and message.get("id") not in seen:
                    seen.add(message.get("id"))
                    context = sum(usage.get(key, 0) or 0 for key in
                                  ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                    requests.append((context, pending))
                    pending = []
            elif entry.get("type") == "user":
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("tool_use_id") in bash_ids:
                        pending.append(result_text(block))
    return requests


def replay(requests, limits, caps, bytes_per_token):
    """한 세션의 실제 읽기 총량과, 출력 빼내기·압축 상한별로 다시 계산한 읽기 총량."""
    actual = sum(context for context, _ in requests)
    # 출력 빼내기: 덜 들어온 토큰은 다음 압축 전까지 뒤따르는 모든 요청에서 덜 읽힌다
    adjusted, carried, previous = [], 0, None
    for context, results in requests:
        if previous is not None and context < previous * COMPACTION_DROP:
            carried = 0
        carried += sum((len(text.encode("utf-8")) - kept_bytes(text, limits)) / bytes_per_token for text in results)
        adjusted.append(max(context - carried, 0))
        previous = context
    totals = {"actual": actual, "offload": sum(adjusted)}
    for cap in caps:
        for name, series in (("cap%d" % cap, [context for context, _ in requests]), ("offload+cap%d" % cap, adjusted)):
            totals[name] = capped_total(series, cap)
    return totals


def capped_total(series, cap):
    """압축 상한 cap 을 둔 톱니 모양 읽기 총량. 각 구간은 그 구간의 첫 문맥 크기에서 다시 자란다.

    압축 한 번은 그 순간의 문맥(약 cap)을 요약하려고 한 번 더 읽는다 — 그 몫을 더한다.
    """
    total, base, previous, done = 0, None, None, 0
    for context in series:
        # 실제 기록에서 문맥이 크게 줄었으면 거기서 새 구간이 시작된다
        if base is None or (previous is not None and context < previous * COMPACTION_DROP):
            base, done = context, 0
        previous = context
        if context <= cap or cap <= base:
            total += context
            continue
        compactions, within = divmod(context - base, cap - base)
        total += base + within + cap * max(compactions - done, 0)
        done = max(done, compactions)
    return total


def main():
    """대화 기록들을 다시 계산해 세션별·합계를 표로 쓴다."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--projects", default=os.path.join(os.path.expanduser("~"), ".claude", "projects"))
    parser.add_argument("--days", type=float, default=30, help="transcripts modified within this many days")
    parser.add_argument("--caps", default="250000,300000,400000", help="compaction caps to try, in tokens")
    parser.add_argument("--bytes-per-token", type=float, default=4.0, help="bytes of tool output per token (estimate)")
    parser.add_argument("--min-requests", type=int, default=20, help="skip sessions shorter than this")
    parser.add_argument("--out", required=True, help="TSV with one row per session and a total row")
    args = parser.parse_args()

    # 출력 상한 같은 값은 게이트 파일에서 읽는다 — 두 곳에 따로 두면 어긋난다
    limits = offload_defaults()
    caps = [int(cap) for cap in args.caps.split(",") if cap.strip()]
    cutoff = time.time() - args.days * 86400
    paths = [path for path in glob.glob(os.path.join(args.projects, "*", "*.jsonl")) if os.path.getmtime(path) >= cutoff]
    rows, grand = [], {}
    for path in sorted(paths):
        requests = read_session(path)
        if len(requests) < args.min_requests:
            continue
        totals = replay(requests, limits, caps, args.bytes_per_token)
        rows.append((os.path.basename(path)[:8], len(requests), totals))
        for key, tokens in totals.items():
            grand[key] = grand.get(key, 0) + tokens
    keys = list(grand)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\t".join(["session", "requests"] + keys) + "\n")
        for session, count, totals in rows:
            handle.write("\t".join([session, str(count)] + ["%d" % totals[key] for key in keys]) + "\n")
        handle.write("\t".join(["TOTAL", str(sum(count for _, count, _ in rows))] + ["%d" % grand[key] for key in keys]) + "\n")
    print("sessions %d (of %d transcripts, %g days, >= %d requests)" % (len(rows), len(paths), args.days, args.min_requests))
    print("limits %s  bytes/token %.1f" % (limits, args.bytes_per_token))
    for key in keys:
        print("%-22s %15d  %5.1f%% less than actual" % (key, grand[key], 100 * (1 - grand[key] / grand["actual"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
