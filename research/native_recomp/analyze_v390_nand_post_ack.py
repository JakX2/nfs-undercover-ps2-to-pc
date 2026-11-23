#!/usr/bin/env python3
"""V390 bounded public original NAND first guest call after two MMIO ACKs."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V390_NAND_POST_ACK guest=([01]) clear=([01]) registered=([01]) masked=([01]) cache=([01]) context=([01])$')
TRIAL=re.compile(r'^V390_NAND_POST_ACK_TRIAL flag=([01]) next=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    cache_any=context_any=0
    all_good=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:
                all_good=False;break
            entries+=1
            guest,clear,registered,masked,cache,context=map(int,m.groups())
            cache_any|=cache;context_any|=context
            all_good=all_good and bool(guest and clear and registered and masked)
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:
                all_good=False;break
            trials+=1
            all_good=all_good and all(v=='1' for v in m.groups())
    return (
        f'V390_NAND_POST_ACK_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'cache_any={cache_any} context_any={context_any} '
        f'next_verified={int(bool(all_good and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V390_NAND_POST_ACK_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V390_NAND_POST_ACK_AUDIT verified=1')
    return 0
if __name__=="__main__":raise SystemExit(main())
