#!/usr/bin/env python3
"""Read-only V406 first-trial call-entry checkpoints around native signal abort.

A bounded counter emits at most 48 guest call indices (49–96) from a
separate V405 native binary. The last index is the last *observed* guest
function entry, not necessarily the crashing instruction or an OS boot.
No guest PC, instructions, register values, pointers, or NAND data leave
the owner-private execution process.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers

ENTRY=re.compile(
    r'^V406_NAND_CHECKPOINT call=(49|[5-8][0-9]|9[0-6]) '
    r'origin=([1-4]) selected=([01]) parent=([01])$')

def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,))
    seen=last=first=mask=sel=parent=0
    expected=49
    good=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if not m:
            continue
        call,origin,selected,par=map(int,m.groups())
        if seen>=48 or call!=expected:
            good=False
            break
        if seen==0:
            first=call
        seen+=1
        expected+=1
        last=call
        mask|=1<<(origin-1)
        sel|=selected
        parent|=par
        if parent and not sel:
            good=False
            break
    contiguous=bool(not overflow and good and seen>0)
    return (
        f'V406_NAND_CHECKPOINT_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'seen={seen} first={first} last={last} mask={mask} '
        f'selected_any={sel} parent_any={parent} '
        f'contiguous={int(contiguous)} '
        f'boundary96={int(contiguous and seen==48 and last==96)} boot_verified=0'
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('owner_private_guest_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    args=p.parse_args()
    try:
        print(inspect(args.owner_private_guest_log,args.native_exit_code))
    except (ValueError,OSError):
        print('V406_NAND_CHECKPOINT_AUDIT inspected=0',file=sys.stderr)
        return 1
    print('V406_NAND_CHECKPOINT_AUDIT inspected=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
