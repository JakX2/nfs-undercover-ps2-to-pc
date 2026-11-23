#!/usr/bin/env python3
"""V359: privacy-safe bounded post-X1 guest-call and IOS status census."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

CALL=re.compile(
    r"^V359_X1_CALL n=([1-9]|1[0-6]) kind=([0-8]) "
    r"pending=([01]) irq=([01]) ee=([01]) replies=([01])$"
)

def inspect(path: Path,rc:int) -> str:
    kind=category(rc)
    size,lines=read_edges(path)
    categories=0
    calls=0
    first_pending=last_pending=irq_any=ee_any=replies_any=0
    for line in lines:
        m=CALL.fullmatch(line)
        if not m:
            continue
        n,which,pending,irq,ee,replies=map(int,m.groups())
        if n!=calls+1:
            # A gap or duplicate cannot provide an ordered, complete
            # original-call trace. Keep the positive contiguous prefix.
            break
        if calls==0:
            first_pending=pending
        last_pending=pending
        calls+=1
        categories|=1<<which
        irq_any|=irq
        ee_any|=ee
        replies_any|=replies
    return (
        f"V359_POST_X1 rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} calls={calls} "
        f"kindmask={categories:03x} pending_first={first_pending} "
        f"pending_last={last_pending} irq_any={irq_any} "
        f"ee_any={ee_any} replies_any={replies_any}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("native_exit",type=int)
    args=p.parse_args()
    try:
        row=inspect(args.private_native_log,args.native_exit)
    except (ValueError,OSError):
        print("V359_X1_AUDIT verified=0",file=sys.stderr)
        return 1
    print(row)
    print("V359_X1_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
