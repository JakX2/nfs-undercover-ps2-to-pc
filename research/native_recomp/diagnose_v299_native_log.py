#!/usr/bin/env python3
"""V299: bounded privacy-safe diagnostics for a failed restored NAND trial.

The original Wii executable, generated C++, and raw native output remain
private to owner CI. Only a fixed-size head/tail sample is inspected, and
only exit categories, size bands and known public instrumentation markers
are emitted. No raw guest output, paths, pointers or instruction words.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

WINDOW = 256 * 1024
PRIOR_LIMIT = 8_000_000

CALLBACK = re.compile(
    r"^V250_CB_BEGIN candidate=1 reply=[01] captured=1$"
)
CHILD = re.compile(
    r"^V289_NAND_ENTRY n=[0-9]{1,4} phase=[01] zero=[01] "
    r"sc=[0-9]{1,3} guest=1 inst=[0-9]{1,18}$"
)
SERVICE = re.compile(
    r"^V296_SERVICE_ENTRY kind=([12]) guest=1 direct=[01] inst=[0-9]{1,18}$"
)
WRITER = re.compile(
    r"^V278_FCA4_ENTRY n=[0-9]{1,4} phase=[01] cb=[01] "
    r"nand=[01] child=[01] sc=[0-9]{1,3} guest=1 inst=[0-9]{1,18}$"
)
EXCEPTION_NAMES = (
    ("std::runtime_error", "runtime"),
    ("std::out_of_range", "range"),
    ("std::bad_alloc", "alloc"),
    ("std::logic_error", "logic"),
)

def size_band(size: int) -> int:
    if size < 0:
        raise ValueError("invalid_size")
    if size <= 1_000_000:
        return 0
    if size <= PRIOR_LIMIT:
        return 1
    if size <= 64_000_000:
        return 2
    return 3

def category(rc: int) -> str:
    if not 0 <= rc <= 255:
        raise ValueError("invalid_rc")
    if rc == 124:
        return "timeout"
    if rc in (125, 126, 127):
        return "launch"
    if rc >= 128:
        return "signal"
    if rc == 0:
        return "zero"
    return "nonzero"

def read_edges(path: Path) -> tuple[int, list[str]]:
    size = path.stat().st_size
    with path.open("rb") as stream:
        prefix = stream.read(min(size, WINDOW))
        suffix = b""
        suffix_start = 0
        if size > WINDOW:
            suffix_start = max(WINDOW, size - WINDOW)
            stream.seek(suffix_start)
            suffix = stream.read(WINDOW)
    # The first and last incomplete records may be mid-line fragments.
    # Drop them rather than manufacturing markers across sample edges.
    front = prefix.decode("utf-8", errors="replace").splitlines()
    if size > WINDOW and prefix and not prefix.endswith(b"\n"):
        front = front[:-1]
    back = suffix.decode("utf-8", errors="replace").splitlines()
    if suffix_start > 0 and suffix and not suffix.startswith(b"\n"):
        back = back[1:]
    return size, front + back

def diagnose(path: Path, rc: int) -> str:
    kind = category(rc)
    size, lines = read_edges(path)
    callback = any(CALLBACK.fullmatch(line) for line in lines)
    child = any(CHILD.fullmatch(line) for line in lines)
    service = [m.group(1) for line in lines if (m := SERVICE.fullmatch(line))]
    writer = any(WRITER.fullmatch(line) for line in lines)
    sample = "\n".join(lines)
    exception = next(
        (name for token, name in EXCEPTION_NAMES if token in sample),
        "unclassified"
    )
    return (
        f"V299_NATIVE_DIAG rc={rc} kind={kind} size_band={size_band(size)} "
        f"over_limit={int(size > PRIOR_LIMIT)} edge_sample=1 "
        f"callback={int(callback)} child={int(child)} "
        f"early={int('1' in service)} late={int('2' in service)} "
        f"writer={int(writer)} exception={exception}"
    )

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log", type=Path)
    p.add_argument("native_exit", type=int)
    a = p.parse_args()
    try:
        report = diagnose(a.private_native_log, a.native_exit)
    except (OSError, ValueError):
        print("V299_NATIVE_DIAG verified=0", file=sys.stderr)
        return 1
    print(report)
    print("V299_NATIVE_DIAG verified=1")
    return 0

if __name__ == "__main__":
    sys.exit(main())
