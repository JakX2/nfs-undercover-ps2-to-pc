#!/usr/bin/env python3
"""V370 bounded original Hollywood flag W1C and pending reply evidence."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

RECORD=re.compile(
    r"^V370_NAND_FLAG_W1C n=([1-9]|1[0-6]) accepted=([01]) "
    r"before=([01]) write_ipc=([01]) remaining=([01]) "
    r"irq=([01]) queued=([01])$"
)

def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    calls=accepted=ipc_write=cleared=retained_any=queued_any=irq_any=0
    for line in lines:
        m=RECORD.fullmatch(line)
        if m is None:
            continue
        n,ok,before,w1c,remaining,irq,queued=map(int,m.groups())
        if n!=calls+1:
            break
        # Hollywood re-samples the live IPC mailbox immediately after
        # W1C; an unacknowledged Y2 can legitimately re-latch IPC_PPC.
        # Do not label that state corrupt or fabricate a successful clear.
        calls+=1
        accepted+=ok
        ipc_write|=w1c
        cleared|=int(bool(before and w1c and not remaining))
        retained_any|=int(bool(before and w1c and remaining))
        queued_any|=queued
        irq_any|=irq
    return (
        f"V370_FLAG_CENSUS rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} writes={calls} "
        f"accepted={accepted} ipc_write={ipc_write} cleared={cleared} "
        f"retained_any={retained_any} queued_any={queued_any} irq_any={irq_any}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        print(inspect(a.private_log,a.native_exit))
    except (OSError,ValueError):
        print("V370_FLAG_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V370_FLAG_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
