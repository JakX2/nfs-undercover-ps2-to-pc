#!/usr/bin/env python3
"""V372 bounded, privacy-safe census of NAND after historical V153 proof."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

RECORD=re.compile(
    r'^V372_NAND_SC_TRIAL phase=1 sc_bridge=([01]) queued=([01]) '
    r'y1=([01]) y2=([01]) flag=([01]) irq=([01]) ee=([01])$'
)

def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    count=bridge_any=queued_any=y1_any=y2_any=flag_any=irq_any=ee_any=0
    for line in lines:
        match=RECORD.fullmatch(line)
        if not match:
            continue
        if count>=16:
            break
        bits=list(map(int,match.groups()))
        count+=1
        bridge_any|=bits[0];queued_any|=bits[1]
        y1_any|=bits[2];y2_any|=bits[3]
        flag_any|=bits[4];irq_any|=bits[5];ee_any|=bits[6]
    return (
        f'V372_NAND_SC_CENSUS rc={rc} kind={kind} size_band={size_band(size)} '
        f'sample_complete={int(size<=WINDOW)} samples={count} '
        f'bridge_any={bridge_any} queued_any={queued_any} '
        f'y1_any={y1_any} y2_any={y2_any} flag_any={flag_any} '
        f'irq_any={irq_any} ee_any={ee_any}'
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_log',type=Path)
    p.add_argument('native_exit',type=int)
    a=p.parse_args()
    try:
        print(inspect(a.private_log,a.native_exit))
    except (OSError,ValueError):
        print('V372_NAND_SC_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V372_NAND_SC_AUDIT verified=1')
    return 0

if __name__=='__main__':
    sys.exit(main())
