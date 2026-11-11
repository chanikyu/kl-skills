#!/usr/bin/env python3
"""파이프라인 단계 사이에 오가는 파일 한 장을 숫자로 보여준다.

    probe.py [--rows N] FILE [FILE...]

디버깅에서 가장 자주 건너뛰는 일이 "이 단계가 무엇을 내놓았는지 숫자로 보기"다.
눈으로 열어 보고 "괜찮아 보인다"로 넘어가면, 빈 칸 두 개나 사라진 행 몇 개는 보이지
않는다. 이 스크립트는 그 확인을 명령 한 줄로 만든다.

읽는 형식과 보여주는 것:

  표 (.tsv .csv)            행 수, 열 이름, 빈 칸이 있는 열과 그 개수, 앞 몇 줄
  JSON (.json)              최상위 종류와 길이, 키 이름
  서열 (.fa .fasta .fna .faa .fas)  레코드 수, 이름 몇 개, 서열 길이 최소·최대·합
  그 밖                      줄 수와 앞 몇 줄

이름 끝에 .gz 가 붙어 있으면 압축을 풀면서 읽는다. 외부 패키지는 쓰지 않는다 —
디버깅 도구가 설치 문제로 안 돌면 정작 필요할 때 쓸 수 없다.
"""

import argparse
import csv
import gzip
import json
import os
import sys

TABLE_SUFFIXES = {".tsv": "\t", ".csv": ","}
SEQUENCE_SUFFIXES = {".fa", ".fasta", ".fna", ".faa", ".fas"}


def open_text(path):
    """압축 여부와 상관없이 글로 연다. 깨진 글자는 바꿔 넣고 계속 읽는다."""
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, encoding="utf-8", errors="replace")


def real_suffix(path):
    """.gz 를 떼고 남은 확장자. samples.tsv.gz 는 .tsv 다."""
    base = path[:-3] if path.endswith(".gz") else path
    return os.path.splitext(base)[1].lower()


def probe_table(path, delimiter, sample_rows):
    """표 파일의 행 수, 열, 빈 칸, 앞부분을 줄 목록으로 돌려준다."""
    with open_text(path) as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader, None)
        if header is None:
            return ["  비어 있다 (머리줄도 없다)"]
        empty_counts = [0] * len(header)
        width_mismatch = 0
        first_rows = []
        row_count = 0
        for row in reader:
            row_count += 1
            # 열 개수가 머리줄과 다른 행은 합치기·자르기 단계에서 생기는 흔한 고장이다.
            if len(row) != len(header):
                width_mismatch += 1
            for column_index, cell in enumerate(row[:len(header)]):
                if cell.strip() == "" or cell.strip().upper() in ("NA", "NAN", "NULL", "NONE"):
                    empty_counts[column_index] += 1
            if len(first_rows) < sample_rows:
                first_rows.append(row)

    lines = ["  행 %d개 × 열 %d개" % (row_count, len(header)),
             "  열: %s" % ", ".join(header)]
    empties = [(name, count) for name, count in zip(header, empty_counts) if count]
    if empties:
        lines.append("  빈 칸: " + ", ".join("%s %d개" % pair for pair in empties))
    else:
        lines.append("  빈 칸: 없음")
    if width_mismatch:
        lines.append("  열 개수가 머리줄과 다른 행: %d개" % width_mismatch)
    for row in first_rows:
        lines.append("    " + " | ".join(row))
    return lines


def probe_json(path):
    """JSON 의 최상위 모양을 줄 목록으로 돌려준다."""
    with open_text(path) as handle:
        try:
            document = json.load(handle)
        except ValueError as error:
            return ["  JSON 으로 읽히지 않는다: %s" % error]
    if isinstance(document, list):
        lines = ["  목록, 항목 %d개" % len(document)]
        if document and isinstance(document[0], dict):
            lines.append("  첫 항목의 키: %s" % ", ".join(list(document[0])[:15]))
        return lines
    if isinstance(document, dict):
        lines = ["  사전, 키 %d개: %s" % (len(document), ", ".join(list(document)[:15]))]
        # 키 아래에 목록이 있으면 그 길이가 대개 "몇 개를 처리했나" 의 답이다.
        for key, nested in list(document.items())[:15]:
            if isinstance(nested, (list, dict)):
                lines.append("    %s: %s %d개" % (key, "목록" if isinstance(nested, list) else "사전",
                                                  len(nested)))
        return lines
    return ["  값 하나: %r" % (document,)]


def probe_sequences(path, sample_rows):
    """서열 파일의 레코드 수와 길이 분포를 줄 목록으로 돌려준다."""
    names, lengths = [], []
    # 아직 첫 '>' 를 못 만났으면 None 이다. 그 앞의 줄은 어느 레코드에도 속하지 않는다.
    current_length = None
    with open_text(path) as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if current_length is not None:
                    lengths.append(current_length)
                names.append(line[1:].split()[0] if line[1:].split() else "(이름 없음)")
                current_length = 0
            elif current_length is not None:
                # 서열은 여러 줄로 감겨 있을 수 있다. 줄마다 더해야 레코드 길이가 된다.
                current_length += len(line.strip())
    if current_length is not None:
        lengths.append(current_length)
    if not names:
        return ["  '>' 로 시작하는 줄이 없다 — 서열 파일이 아니거나 비어 있다"]
    lines = ["  레코드 %d개" % len(names),
             "  서열 길이: 최소 %d, 최대 %d, 합 %d" % (min(lengths), max(lengths), sum(lengths)),
             "  이름: %s" % ", ".join(names[:sample_rows])]
    empty_records = sum(1 for length in lengths if length == 0)
    if empty_records:
        lines.append("  서열이 빈 레코드: %d개" % empty_records)
    return lines


def probe_plain(path, sample_rows):
    """형식을 모르는 파일은 줄 수와 앞부분만 보여준다."""
    line_count, first_lines = 0, []
    with open_text(path) as handle:
        for line in handle:
            line_count += 1
            if len(first_lines) < sample_rows:
                first_lines.append(line.rstrip("\n"))
    return ["  줄 %d개" % line_count] + ["    " + line for line in first_lines]


def probe(path, sample_rows):
    """파일 한 장을 형식에 맞게 읽어 보고서 줄 목록을 만든다."""
    if not os.path.isfile(path):
        return ["%s" % path, "  없다"]
    size_bytes = os.path.getsize(path)
    lines = ["%s  (%d바이트)" % (path, size_bytes)]
    if size_bytes == 0:
        return lines + ["  비어 있다 — 앞 단계가 아무것도 쓰지 않았다"]
    suffix = real_suffix(path)
    try:
        if suffix in TABLE_SUFFIXES:
            return lines + probe_table(path, TABLE_SUFFIXES[suffix], sample_rows)
        if suffix == ".json":
            return lines + probe_json(path)
        if suffix in SEQUENCE_SUFFIXES:
            return lines + probe_sequences(path, sample_rows)
        return lines + probe_plain(path, sample_rows)
    except (OSError, EOFError, csv.Error) as error:
        # 파일이 깨져 있는 것 자체가 단계의 출력에 대한 답이다. 감추지 않고 보고한다.
        return lines + ["  읽다가 멈췄다: %s" % error]


def main(argv=None):
    """명령줄 입구. 파일마다 한 덩어리씩 출력한다."""
    parser = argparse.ArgumentParser(description="파이프라인 단계 사이의 파일을 숫자로 본다.")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--rows", type=int, default=3, help="앞부분을 몇 줄 보여줄지 (기본 3)")
    options = parser.parse_args(argv)
    for index, path in enumerate(options.files):
        if index:
            print()
        print("\n".join(probe(path, options.rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
