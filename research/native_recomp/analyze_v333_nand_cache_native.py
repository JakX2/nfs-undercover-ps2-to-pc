#!/usr/bin/env python3
"""V333: bounded, privacy-safe NAND cache syscall completion evidence.

The original NAND IOS request can enter the installed syscall vector
without actually returning. Report the authenticated V331 completion
marker separately from original guest entry markers. No private log
lines, registers, request buffers, or native game code are printed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from diagnose_v299_native_log import (
    CHILD, SERVICE, WRITER, WINDOW, category, read_edges, size_band
)

DONE="V331_NAND_CACHE_SYSCALL verified=1"

def inspect(path: Path, rc: int) -> str:
    kind=category(rc)
    size, lines=read_edges(path)
    completed=sum(line==DONE for line in lines)
    child=any(CHILD.fullmatch(line) for line in lines)
    services=[m.group(1) for line in lines if (m:=SERVICE.fullmatch(line))]
    writer=any(WRITER.fullmatch(line) for line in lines)
    return (
        f"V333_NAND_CACHE rc={rc} kind={kind} size_band={size_band(size)} "
        f"complete={int(size<=WINDOW)} child={int(child)} "
        f"early={int('1' in services)} late={int('2' in services)} "
        f"writer={int(writer)} sc_done={min(completed,9999)}"
    )

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        summary=inspect(a.private_native_log,a.native_exit)
    except (OSError,ValueError):
        print("V333_CACHE_AUDIT verified=0",file=sys.stderr)
        return 1
    print(summary)
    print("V333_CACHE_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
