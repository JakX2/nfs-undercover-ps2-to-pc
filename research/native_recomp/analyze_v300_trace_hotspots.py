#!/usr/bin/env python3
"""V300: public-marker and guest-PC histogram from oversized private NAND logs.

Only the bounded head/tail records from V299 are inspected. A marker must
exist as a literal in the independently authored public C++ harness before
its name may leave CI; arbitrary game output is never echoed. No raw lines,
game bytes, translated instructions, paths or pointers are published.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys

from diagnose_v299_native_log import read_edges, size_band

MARKER = re.compile(r"^V[0-9]{2,3}_[A-Z][A-Z0-9_]{1,45}$")
PC = re.compile(r"(?:^| )pc=([0-9a-f]{8})(?=$| )")
SOURCE_MARKER = re.compile(r"V[0-9]{2,3}_[A-Z][A-Z0-9_]{1,45}")

def analyze(log_path: Path, public_harness: str) -> list[str]:
    if not public_harness or len(public_harness) > 24_000_000:
        raise ValueError("public_source_geometry")
    allowed = set(SOURCE_MARKER.findall(public_harness))
    size, sampled = read_edges(log_path)
    counts: Counter[str] = Counter()
    pcs: Counter[int] = Counter()
    unknown = 0
    for line in sampled:
        marker = line.partition(" ")[0]
        if marker in allowed and MARKER.fullmatch(marker):
            counts[marker] += 1
            m = PC.search(line)
            if m:
                value = int(m.group(1),16)
                if 0x80000000 <= value < 0x81800000:
                    pcs[value] += 1
        elif line:
            unknown += 1
    rows = [
        f"V300_TRACE_SAMPLE size_band={size_band(size)} "
        f"sample_lines={len(sampled)} matched={sum(counts.values())} "
        f"unmatched={unknown} distinct={len(counts)} "
        f"distinct_pc={len(pcs)}"
    ]
    for rank, (marker, n) in enumerate(sorted(
        counts.items(), key=lambda kv:(-kv[1],kv[0]))[:5],1):
        rows.append(f"V300_TRACE_MARKER rank={rank} name={marker} hits={n}")
    for rank, (pc,n) in enumerate(sorted(
        pcs.items(), key=lambda kv:(-kv[1],kv[0]))[:5],1):
        rows.append(f"V300_TRACE_PC rank={rank} pc={pc:08x} hits={n}")
    return rows

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("compiled_public_harness",type=Path)
    a=p.parse_args()
    try:
        reports=analyze(
            a.private_native_log,
            a.compiled_public_harness.read_text(encoding="utf-8",errors="replace")
        )
    except (OSError,ValueError):
        print("V300_TRACE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("\n".join(reports))
    print("V300_TRACE_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
