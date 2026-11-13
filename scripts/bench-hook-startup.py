#!/usr/bin/env python3
"""Measure how long a hook takes to start, Rust gate vs Python gate.

The number that matters is the DIFFERENCE, not either absolute: both include the
same fork/exec overhead from spawning a process, which a hook pays either way.
Run it on the machine you care about — the gap is dominated by interpreter
startup, which varies by Python version and platform.

  python3 scripts/bench-hook-startup.py [--root DIR] [-n 30]

--root defaults to the repo this script lives in, so it measures the binaries in
bin/. Point it at an installed plugin directory to measure what is deployed.
"""
import argparse
import os
import pathlib
import statistics
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parent.parent


def measure(cmd, n):
    samples = []
    for _ in range(n):
        start = time.perf_counter()
        subprocess.run(cmd, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples), min(samples), max(samples)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO),
                    help="plugin root holding bin/ and hooks/ (default: this repo)")
    ap.add_argument("-n", type=int, default=30, help="runs per variant (default: 30)")
    args = ap.parse_args()

    root = pathlib.Path(args.root).expanduser().resolve()
    launcher = root / "hooks" / "run.sh"
    if not launcher.exists():
        sys.exit(f"no hooks/run.sh under {root}")

    # Ask the launcher which target this machine uses, instead of guessing here.
    target = subprocess.run(["sh", str(launcher), "--print-target"],
                            capture_output=True, text=True).stdout.strip()
    if not target:
        sys.exit("this platform has no prebuilt binary, so there is nothing to compare")

    rust = root / "bin" / f"kl-gate-{target}"
    if not rust.exists():
        sys.exit(f"missing {rust} - has CI built it yet?")

    with tempfile.TemporaryDirectory() as tmp:
        noop = pathlib.Path(tmp) / "noop_gate.py"
        noop.write_text("import sys\n")  # read nothing, do nothing: startup cost only

        rows = [
            ("rust kl-gate (unknown gate: no work, no output)", [str(rust), "bench-noop"]),
            ("python3 empty gate script", [sys.executable, str(noop)]),
        ]
        results = []
        for label, cmd in rows:
            med, lo, hi = measure(cmd, args.n)
            results.append((label, med, lo, hi))
            print(f"{label:50s} median {med:6.1f} ms  (min {lo:.1f} / max {hi:.1f})")

    gap = results[1][1] - results[0][1]
    print(f"\ngap (python - rust, medians): {gap:.1f} ms per hook invocation")
    print(f"n={args.n} per variant, target={target}")
    print(f"python={sys.version.split()[0]}  machine={os.uname().sysname}/{os.uname().machine}")
    # 홈 폴더는 ~ 로 줄인다: 결과 파일을 커밋하면 컴퓨터 사용자 이름이 공개 저장소에 남는다(2026-11-13)
    print(f"root={str(root).replace(os.path.expanduser('~'), '~', 1)}")


if __name__ == "__main__":
    main()
