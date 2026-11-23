#!/usr/bin/env python3
"""V399 original-free temporal return-PC/callsite witness, without BLR claim."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from analyze_v398_nand_return_site import ENTRY as ENTRY398
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers

ENTRY=re.compile(
    r'^V399_NAND_RETURN_ORDER site=([01]) mapped=([01]) bctrl=([01]) '
    r'isfs_after=([01]) parent_after=([01]) ordered=([01]) blr_verified=0$')
TRIAL=re.compile(r'^V399_NAND_RETURN_TRIAL ordered=([01]) completed=([01])$')

def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY398,ENTRY,TRIAL))
    entries=trials=site_count=mapped_count=bctrl_count=isfs_count=parent_count=ordered_count=0
    phase=0
    saved_site=saved_mapped=saved_pre=last_order=0
    good=True
    for line in lines:
        m=ENTRY398.fullmatch(line)
        if m:
            if phase!=0 or entries>=16:
                good=False
                break
            samples,saved_site,saved_mapped,saved_pre,valid_lr=map(int,m.groups())
            good=good and bool(valid_lr and (not saved_site or samples) and
                               (not saved_mapped or saved_site) and
                               (not saved_pre or saved_site))
            phase=1
            continue
        m=ENTRY.fullmatch(line)
        if m:
            if phase!=1 or entries>=16:
                good=False
                break
            site,mapped,bctrl,isfs,parent,ordered=map(int,m.groups())
            good=good and (site,mapped)==(saved_site,saved_mapped)
            good=good and ordered==int(bool(site and mapped and isfs))
            good=good and (not isfs or (site and mapped and saved_pre))
            good=good and (not parent or (site and mapped and saved_pre))
            good=good and (not bctrl or site)
            entries+=1
            site_count+=site
            mapped_count+=mapped
            bctrl_count+=bctrl
            isfs_count+=isfs
            parent_count+=parent
            ordered_count+=ordered
            last_order=ordered
            phase=2
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if phase!=2 or trials>=16:
                good=False
                break
            ordered,complete=map(int,m.groups())
            good=good and bool(complete and ordered==last_order)
            trials+=1
            phase=0
    valid=bool(not overflow and good and phase==0 and entries==trials and entries)
    return (
        f"V399_NAND_RETURN_CENSUS rc={rc} kind={category(rc)} "
        f"size_band={size_band(size)} sample_complete={int(size<=WINDOW)} "
        f"entries={entries} trials={trials} site_trials={site_count} "
        f"mapped_trials={mapped_count} bctrl_trials={bctrl_count} "
        f"isfs_after_trials={isfs_count} parent_after_trials={parent_count} "
        f"ordered_trials={ordered_count} lineage_verified={int(valid)} blr_verified=0"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print("V399_NAND_RETURN_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V399_NAND_RETURN_AUDIT verified=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
