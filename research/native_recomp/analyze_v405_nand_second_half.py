#!/usr/bin/env python3
"""V405 bounded census of original Wii guest calls 49–96 by LR region."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers

COUNT=r'([0-9]|[1-3][0-9]|4[0-8])'
ENTRY=re.compile(
    r'^V405_NAND_SECOND_HALF tail_calls='+COUNT+
    r' selected='+COUNT+r' isfs='+COUNT+r' parent='+COUNT+
    r' other='+COUNT+r' nand='+COUNT+r' cache='+COUNT+r'$')
TRIAL=re.compile(r'^V405_NAND_SECOND_TRIAL tail_calls='+COUNT+r' completed=([01])$')

def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,TRIAL))
    entries=trials=complete48=0
    max_tail=0
    totals=[0]*6
    good=True
    last=0
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:
                good=False
                break
            calls,selected,isfs,parent,other,nand,cache=map(int,m.groups())
            good=good and (selected+isfs+parent+other==calls and
                           nand<=calls and cache<=calls)
            entries+=1
            max_tail=max(max_tail,calls)
            complete48+=int(calls==48)
            totals=[x+y for x,y in zip(totals,
                                        (selected,isfs,parent,other,nand,cache))]
            last=calls
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if entries<=trials or trials>=16:
                good=False
                break
            calls,completed=map(int,m.groups())
            good=good and bool(calls==last and completed)
            trials+=1
    valid=bool(not overflow and good and entries==trials and entries)
    return (
        f'V405_NAND_SECOND_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} max_tail={max_tail} '
        f'full48_trials={complete48} selected_total={totals[0]} '
        f'isfs_total={totals[1]} parent_total={totals[2]} '
        f'other_total={totals[3]} nand_total={totals[4]} '
        f'cache_total={totals[5]} lineage_verified={int(valid)} boot_verified=0'
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V405_NAND_SECOND_AUDIT inspected=0',file=sys.stderr)
        return 1
    print('V405_NAND_SECOND_AUDIT inspected=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
