#!/usr/bin/env python3
"""V365: bounded positive-only IRQ eligibility census from private Wii log."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

ENTRY=re.compile(
    r"^V365_IRQ_READY n=([1-9]|1[0-6]) eligible=([01]) "
    r"safe=([01]) installed=([01]) ready=([01])$"
)

def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    count=eligible_any=safe_any=installed_any=ready_any=0
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m is None:
            continue
        n,eligible,safe,installed,ready=map(int,m.groups())
        if n!=count+1 or ready!=int(bool(eligible and safe and installed)):
            break
        count+=1
        eligible_any|=eligible
        safe_any|=safe
        installed_any|=installed
        ready_any|=ready
    return (
        f"V365_IRQ_CENSUS rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} samples={count} "
        f"eligible_any={eligible_any} safe_any={safe_any} "
        f"installed_any={installed_any} ready_any={ready_any}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        print(inspect(a.private_log,a.native_exit))
    except (OSError,ValueError):
        print("V365_IRQ_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V365_IRQ_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
