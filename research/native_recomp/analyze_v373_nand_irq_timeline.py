#!/usr/bin/env python3
"""V373 privacy-safe, bounded timeline summary for NAND IOS IRQ readiness."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW, category, read_edges, size_band

RECORD = re.compile(
    r"^V373_NAND_IRQ_TIMELINE n=([1-9]|[1-8][0-9]|9[0-6]) "
    r"ee=([01]) irq=([01]) eligible=([01]) safe=([01]) "
    r"installed=([01]) ready=([01]) y1=([01]) y2=([01]) "
    r"flag=([01]) queued=([01])$"
)

def inspect(path:Path, rc:int) -> str:
    kind=category(rc)
    size,lines=read_edges(path)
    count=0
    first_ee=first_irq=first_ready=0
    ee_any=irq_any=eligible_any=safe_any=installed_any=0
    y1_any=y2_any=flag_any=queued_any=0
    for line in lines:
        match=RECORD.fullmatch(line)
        if not match:
            continue
        n,ee,irq,eligible,safe,installed,ready,y1,y2,flag,queued=map(int,match.groups())
        if n!=count+1:
            break
        count+=1
        if ee and not first_ee: first_ee=n
        if irq and not first_irq: first_irq=n
        if ready and not first_ready: first_ready=n
        ee_any|=ee; irq_any|=irq; eligible_any|=eligible
        safe_any|=safe; installed_any|=installed
        y1_any|=y1; y2_any|=y2; flag_any|=flag; queued_any|=queued
    return (
        f"V373_IRQ_CENSUS rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} samples={count} "
        f"first_ee={first_ee} first_irq={first_irq} first_ready={first_ready} "
        f"ee_any={ee_any} irq_any={irq_any} eligible_any={eligible_any} "
        f"safe_any={safe_any} installed_any={installed_any} "
        f"y1_any={y1_any} y2_any={y2_any} flag_any={flag_any} queued_any={queued_any}"
    )

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_log",type=Path)
    parser.add_argument("native_exit",type=int)
    a=parser.parse_args()
    try:
        print(inspect(a.private_log,a.native_exit))
    except (OSError,ValueError):
        print("V373_IRQ_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V373_IRQ_AUDIT verified=1")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
