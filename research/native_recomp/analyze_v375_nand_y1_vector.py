#!/usr/bin/env python3
"""V375 privacy-safe actual NAND Y1 vector entry audit."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

LINE=re.compile(
    r'^V375_NAND_VECTOR n=([1-9]|1[0-6]) y1=([01]) safe=([01]) '
    r'installed=([01]) entered=([01]) saved=([01]) regs=([01]) '
    r'irq_masked=([01]) queued=([01])$'
)

def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    count=eligible_any=safe_any=installed_any=entered_any=saved_any=0
    regs_any=masked_any=queued_any=0
    for line in lines:
        m=LINE.fullmatch(line)
        if not m:
            continue
        n,y1,safe,installed,entered,saved,regs,masked,queued=map(int,m.groups())
        if (n!=count+1 or y1!=1 or
            (entered and not(safe and installed and saved and regs and masked)) or
            (saved and not entered) or (masked and not entered)):
            break
        count+=1
        eligible_any|=y1; safe_any|=safe;installed_any|=installed
        entered_any|=entered; saved_any|=saved;regs_any|=regs
        masked_any|=masked;queued_any|=queued
    return (
        f'V375_NAND_VECTOR_CENSUS rc={rc} kind={kind} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'samples={count} eligible_any={eligible_any} safe_any={safe_any} '
        f'installed_any={installed_any} entered_any={entered_any} '
        f'saved_any={saved_any} regs_any={regs_any} '
        f'masked_any={masked_any} queued_any={queued_any} '
        'handler_executed=0'
    )

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_log',type=Path)
    parser.add_argument('native_exit',type=int)
    args=parser.parse_args()
    try:
        print(inspect(args.private_log,args.native_exit))
    except (OSError,ValueError):
        print('V375_NAND_VECTOR_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V375_NAND_VECTOR_AUDIT verified=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
