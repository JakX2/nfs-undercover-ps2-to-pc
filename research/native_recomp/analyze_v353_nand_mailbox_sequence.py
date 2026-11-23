#!/usr/bin/env python3
"""V353: read-only, privacy-safe original NAND native IOS mailbox sequence.

The owner-original binary writes fixed public V352 status markers to its
private log. This classifier exposes only the tested register category,
64-byte pointer validation, accepted native bus transitions, and X1 queue
status. Missing markers in a bounded sample are not negative execution proof.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

from diagnose_v299_native_log import WINDOW, category, read_edges, size_band

MARKER=re.compile(
    r"^V352_NAND_BUS kind=([12]) mapped=([01]) accepted=([01]) queued=([01])$"
)

def inspect(path: Path, rc: int) -> str:
    kind=category(rc)
    size, lines=read_edges(path)
    msg=ctrl=queued=invalid=0
    chain=0
    for line in lines:
        match=MARKER.fullmatch(line)
        if match is None:
            continue
        which,mapped,accepted,request=map(int,match.groups())
        # These shapes cannot be produced by the original-free writer.
        if (which==2 and not mapped) or (not mapped and (accepted or request)):
            continue
        if which==1:
            if not mapped or not accepted:
                invalid=1
            else:
                msg=1
                if chain==0:
                    chain=1
        elif which==2:
            if not accepted:
                invalid=1
            else:
                ctrl=1
                if request:
                    queued=1
                if chain==1 and request:
                    chain=2
    return (
        f"V353_NAND_MAILBOX rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} msg={msg} ctrl={ctrl} "
        f"queued={queued} invalid={invalid} chain={chain}"
    )

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("native_exit",type=int)
    args=p.parse_args()
    try:
        row=inspect(args.private_native_log,args.native_exit)
    except (OSError,ValueError):
        print("V353_MAILBOX_AUDIT verified=0",file=sys.stderr)
        return 1
    print(row)
    print("V353_MAILBOX_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
