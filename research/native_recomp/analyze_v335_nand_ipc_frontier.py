#!/usr/bin/env python3
"""V335: read-only evidence for genuine NAND IPC submit successor calls.

Only exact original request caller/target pairs are counted. The public
report states what was positively observed in the bounded private log;
missing markers never establish that a native call did not execute.
No original code, request contents, guest registers, or raw logs escape.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from diagnose_v299_native_log import WINDOW, category, read_edges, size_band

DONE = "V331_NAND_CACHE_SYSCALL verified=1"
CALL = re.compile(r"^V98_DEPENDENCY pc=([0-9a-f]{8}) lr=([0-9a-f]{8})$")
# Verified entry/callsite pairs from the original IOS request callgraph:
# OSDisableInterrupts, IPC queue helper, send register, control read.
TARGETS = (
    (0x805265AC, 0x80519640),
    (0x8051AFE0, 0x805196D4),
    (0x8051906C, 0x80519780),
    (0x8051905C, 0x805197B8),
)

def inspect(path: Path, rc: int) -> str:
    kind = category(rc)
    size, lines = read_edges(path)
    seen = [False] * len(TARGETS)
    cache_done = 0
    ordered = 0
    for line in lines:
        if line == DONE:
            cache_done = min(cache_done + 1, 9999)
            continue
        match = CALL.fullmatch(line)
        if match is None:
            continue
        pair = (int(match.group(1), 16), int(match.group(2), 16))
        for index, expected in enumerate(TARGETS):
            if pair == expected:
                seen[index] = True
        if cache_done and ordered < len(TARGETS) and pair == TARGETS[ordered]:
            ordered += 1
    return (
        f"V335_IPC_FRONTIER rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size <= WINDOW)} sc_done={cache_done} "
        f"irq={int(seen[0])} queue={int(seen[1])} "
        f"send={int(seen[2])} ctrl={int(seen[3])} chain={ordered}"
    )

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_native_log", type=Path)
    parser.add_argument("native_exit", type=int)
    args = parser.parse_args()
    try:
        report = inspect(args.private_native_log, args.native_exit)
    except (OSError, ValueError):
        print("V335_IPC_AUDIT verified=0", file=sys.stderr)
        return 1
    print(report)
    print("V335_IPC_AUDIT verified=1")
    return 0

if __name__ == "__main__":
    sys.exit(main())
