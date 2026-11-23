#!/usr/bin/env python3
"""V367: privacy-safe bounded genuine NAND interrupt mask write census."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

ENTRY=re.compile(
    r"^V367_NAND_IRQ_MASK n=([1-9]|1[0-6]) kind=([12]) "
    r"accepted=([01]) irq=([01])$"
)

def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    calls=pi=ppc=accepted=irq_any=0
    for line in lines:
        m=ENTRY.fullmatch(line)
        if not m:
            continue
        n,which,ok,irq=map(int,m.groups())
        if n!=calls+1:
            break
        calls+=1
        pi+=int(which==1)
        ppc+=int(which==2)
        accepted+=ok
        irq_any|=irq
    return (
        f"V367_NAND_MASK rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} writes={calls} "
        f"pi={pi} ppc={ppc} accepted={accepted} irq_any={irq_any}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        print(inspect(a.private_native_log,a.native_exit))
    except (OSError,ValueError):
        print("V367_MASK_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V367_MASK_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
