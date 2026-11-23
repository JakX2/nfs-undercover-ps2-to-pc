#!/usr/bin/env python3
"""V369 bounded privacy-safe post-ACK Wii register write classes."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

RECORD=re.compile(
    r"^V369_POST_ACK_MMIO n=([1-9]|[12][0-9]|3[0-2]) "
    r"kind=([0-5]) legacy=([01]) readable=([01]) irq=([01])$"
)
def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    calls=mask=flag=ctrl=msg=other=0
    last=kindmask=legacy_any=readable_any=irq_any=0
    for line in lines:
        m=RECORD.fullmatch(line)
        if m is None:
            continue
        n,which,legacy,readable,irq=map(int,m.groups())
        if n!=calls+1:
            break
        calls+=1
        last=which
        kindmask|=1<<which
        mask+=int(which in (1,2))
        flag+=int(which==3)
        ctrl+=int(which==4)
        msg+=int(which==5)
        other+=int(which==0)
        legacy_any|=legacy
        readable_any|=readable
        irq_any|=irq
    return (
        f"V369_POST_ACK_CENSUS rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} writes={calls} "
        f"kindmask={kindmask:02x} last={last} mask={mask} flag={flag} "
        f"ctrl={ctrl} msg={msg} other={other} legacy_any={legacy_any} "
        f"readable_any={readable_any} irq_any={irq_any}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        print(inspect(a.private_log,a.native_exit))
    except (OSError,ValueError):
        print("V369_MMIO_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V369_MMIO_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
