#!/usr/bin/env python3
"""V319: proof-oriented native entry census for authenticated NAND AOT calls.

Read only a bounded head/tail sample from the ephemeral private V310
native log. A positive observed original guest-PC entry can corroborate
execution; absence is NOT proof of non-execution, especially if sampling
is incomplete. Never print guest register contents, raw logs, or code.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

MARKER=re.compile(
    r"^V98_DEPENDENCY pc=([0-9a-f]{8}) lr=[0-9a-f]{8}$"
)
TARGETS={
    0x804F2064:"helper41",
    0x80519BCC:"helper64",
    0x805195EC:"ios_request",
    0x8051AD38:"allocator_tail",
    0x80522294:"flush",
    0x80545100:"branch_a",
    0x8054514C:"branch_b",
}

def inspect(path:Path, rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    seen={pc:0 for pc in TARGETS}
    matches=0
    for line in lines:
        m=MARKER.fullmatch(line)
        if not m:
            continue
        pc=int(m.group(1),16)
        if pc not in seen:
            continue
        matches+=1
        seen[pc]=min(99999,seen[pc]+1)
    fields=" ".join(f"{name}={int(seen[pc]>0)}" for pc,name in TARGETS.items())
    return (
        f"V319_NATIVE_ENTRIES rc={rc} kind={kind} "
        f"size_band={size_band(size)} complete={int(size<=WINDOW)} "
        f"known_markers={min(99999,matches)} {fields}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        report=inspect(a.private_native_log,a.native_exit)
    except (OSError,ValueError):
        print("V319_ENTRY_AUDIT verified=0",file=sys.stderr)
        return 1
    print(report)
    print("V319_ENTRY_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
