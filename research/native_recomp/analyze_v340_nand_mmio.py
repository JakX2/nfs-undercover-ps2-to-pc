#!/usr/bin/env python3
"""V340: privacy-safe NAND-phase MMIO route census from ephemeral native log.

All output is fixed bounded categories, never guest instructions, addresses,
values, paths, private logs or proprietary generated C++.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW, category, read_edges, size_band

MMIO=re.compile(
    r"^V340_NAND_MMIO n=(?:[1-9]|1[0-6]) kind=[0-4] "
    r"ack=[01] submit=[01] send=[01] readable=[01]$"
)
FIELDS=re.compile(
    r"^V340_NAND_MMIO n=([0-9]+) kind=([0-4]) "
    r"ack=([01]) submit=([01]) send=([01]) readable=([01])$"
)

def inspect(path: Path, rc: int) -> str:
    kind=category(rc)
    size, lines=read_edges(path)
    counts=[0]*5
    old=[0,0,0]
    readable=0
    valid=0
    for line in lines:
        if not MMIO.fullmatch(line):
            continue
        match=FIELDS.fullmatch(line)
        assert match is not None
        _,kind_id,ack,submit,send,read=map(int,match.groups())
        counts[kind_id]+=1
        old[0]|=ack
        old[1]|=submit
        old[2]|=send
        readable+=read
        valid+=1
    return (
        f"V340_MMIO_CENSUS rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} observed={min(valid,9999)} "
        f"other={min(counts[0],9999)} msg={min(counts[1],9999)} "
        f"ctrl={min(counts[2],9999)} mask={min(counts[3],9999)} "
        f"flag={min(counts[4],9999)} old_ack={old[0]} "
        f"old_submit={old[1]} old_send={old[2]} "
        f"readable={min(readable,9999)}"
    )

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_native_log",type=Path)
    parser.add_argument("native_exit",type=int)
    args=parser.parse_args()
    try:
        summary=inspect(args.private_native_log,args.native_exit)
    except (OSError,ValueError):
        print("V340_MMIO_AUDIT verified=0",file=sys.stderr)
        return 1
    print(summary)
    print("V340_MMIO_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
