#!/usr/bin/env python3
"""V397 sanitized bounded LR callsite origin census, not return proof."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers
ENTRY=re.compile(
    r'^V397_NAND_ORIGINS mask=([1-9]|1[0-5]) last=([1-4]) '
    r'calls=([1-9]|1[0-9]|2[0-4]) selected_any=([01]) '
    r'isfs_any=([01]) parent_any=([01]) other_any=([01]) same_lr_any=([01])$')
TRIAL=re.compile(r'^V397_NAND_ORIGINS_TRIAL completed=([01]) stopped=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,TRIAL))
    entries=trials=last=mask_union=same_lr_any=0
    selected_any=isfs_any=parent_any=other_any=0
    all_cap=True
    good=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:
                good=False
                break
            entries+=1
            mask,origin,calls,selected,isfs,parent,other,same=map(int,m.groups())
            good=good and bool(mask&(1<<(origin-1)))
            good=good and (selected,isfs,parent,other)==tuple(
                int(bool(mask&(1<<i))) for i in range(4))
            all_cap=all_cap and calls==24
            mask_union|=mask
            same_lr_any|=same
            selected_any|=selected
            isfs_any|=isfs
            parent_any|=parent
            other_any|=other
            last=origin
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:
                good=False
                break
            trials+=1
            completed,stopped=map(int,m.groups())
            good=good and bool(completed and stopped and last)
    valid=bool(not overflow and good and entries==trials and entries)
    return (f"V397_NAND_ORIGINS_CENSUS rc={rc} kind={category(rc)} "
            f"size_band={size_band(size)} sample_complete={int(size<=WINDOW)} "
            f"entries={entries} trials={trials} mask={mask_union} "
            f"full_cap_all={int(all_cap and bool(entries))} "
            f"selected_any={selected_any} isfs_any={isfs_any} "
            f"parent_any={parent_any} other_any={other_any} same_lr_any={same_lr_any} "
            f"lineage_verified={int(valid)} return_verified=0")
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print("V397_NAND_ORIGINS_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V397_NAND_ORIGINS_AUDIT verified=1")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
