#!/usr/bin/env python3
"""V385 classify only native NAND ARMMSG mail coherency, no game addresses."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

MARKER=re.compile(r'^V385_NAND_ARMMSG_MIRROR coherent=([01]) y1=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    count=0
    good=True
    coherent_any=y1_any=0
    for line in lines:
        m=MARKER.fullmatch(line)
        if m:
            if count>=16:
                good=False;break
            count+=1
            coherent,y1=map(int,m.groups())
            coherent_any|=coherent;y1_any|=y1
            good=good and bool(coherent and y1)
    return (
        f'V385_NAND_ARMMSG_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'samples={count} coherent_any={coherent_any} y1_any={y1_any} '
        f'mailbox_verified={int(bool(good and count and coherent_any and y1_any))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V385_NAND_ARMMSG_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V385_NAND_ARMMSG_AUDIT verified=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
