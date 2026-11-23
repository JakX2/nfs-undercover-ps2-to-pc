#!/usr/bin/env python3
"""V361: privacy-safe real Starlet pump results after an original NAND X1."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

LINE=re.compile(
    r"^V361_NAND_IOS_YIELD n=([1-9]|1[0-6]) mapped=([01]) "
    r"pump=([0-9]|1[0-9]) pending=([01]) irq=([01]) "
    r"eligible=([01]) replies=([01])$"
)

def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    count=first_pump=last_pump=0
    pending_first=pending_last=0
    irq_any=eligible_any=replies_any=0
    for line in lines:
        m=LINE.fullmatch(line)
        if m is None:
            continue
        n,mapped,pump,pending,irq,eligible,replies=map(int,m.groups())
        if n!=count+1 or mapped!=1 or (eligible and not irq):
            break
        if count==0:
            first_pump=pump
            pending_first=pending
        count+=1
        last_pump=pump
        pending_last=pending
        irq_any|=irq
        eligible_any|=eligible
        replies_any|=replies
    return (
        f"V361_IOS_YIELD rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} steps={count} "
        f"first_pump={first_pump} last_pump={last_pump} "
        f"pending_first={pending_first} pending_last={pending_last} "
        f"irq_any={irq_any} eligible_any={eligible_any} replies_any={replies_any}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        print(inspect(a.private_log,a.native_exit))
    except (OSError,ValueError):
        print("V361_IOS_YIELD_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V361_IOS_YIELD_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
