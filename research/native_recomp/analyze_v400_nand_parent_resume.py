#!/usr/bin/env python3
"""V400 bounded original _isfsFuncCb parent-return site and follow-on call census."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from analyze_v398_nand_return_site import ENTRY as ENTRY398
from analyze_v399_nand_return_order import ENTRY as ENTRY399
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers
ENTRY=re.compile(
    r'^V400_NAND_PARENT_RESUME site=([01]) mapped=([01]) linked=([01]) '
    r'selected_first=([01]) parent_after=([01]) ordered=([01]) blr_verified=0$')
TRIAL=re.compile(r'^V400_NAND_PARENT_TRIAL ordered=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY398,ENTRY399,ENTRY,TRIAL))
    phase=entries=trials=0
    selected_site=selected_mapped=last_order=0
    site_count=mapped_count=linked_count=first_count=parent_count=ordered_count=0
    valid=True
    for line in lines:
        m=ENTRY398.fullmatch(line)
        if m:
            if phase!=0 or entries>=16:
                valid=False
                break
            samples,selected_site,selected_mapped,pre,lr=map(int,m.groups())
            valid=valid and bool(lr and (not selected_site or samples) and
                                  (not selected_mapped or selected_site))
            phase=1
            continue
        m=ENTRY399.fullmatch(line)
        if m:
            if phase!=1:
                valid=False
                break
            site,mapped,bctrl,isfs,parent,order=map(int,m.groups())
            valid=valid and (site,mapped)==(selected_site,selected_mapped)
            phase=2
            continue
        m=ENTRY.fullmatch(line)
        if m:
            if phase!=2 or entries>=16:
                valid=False
                break
            site,mapped,linked,first,after,ordered=map(int,m.groups())
            valid=valid and bool((not mapped or site) and
                   (not linked or site) and
                   (not first or (site and selected_site and selected_mapped)) and
                   (not after or (site and mapped)) and
                   ordered==int(bool(site and mapped and first and after)))
            entries+=1
            site_count+=site
            mapped_count+=mapped
            linked_count+=linked
            first_count+=first
            parent_count+=after
            ordered_count+=ordered
            last_order=ordered
            phase=3
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if phase!=3 or trials>=16:
                valid=False
                break
            order,complete=map(int,m.groups())
            valid=valid and bool(complete and order==last_order)
            trials+=1
            phase=0
    verified=bool(not overflow and valid and phase==0 and entries==trials and entries)
    return (
        f"V400_NAND_PARENT_CENSUS rc={rc} kind={category(rc)} "
        f"size_band={size_band(size)} sample_complete={int(size<=WINDOW)} "
        f"entries={entries} trials={trials} site_trials={site_count} "
        f"mapped_trials={mapped_count} linked_trials={linked_count} "
        f"selected_first_trials={first_count} parent_after_trials={parent_count} "
        f"ordered_trials={ordered_count} lineage_verified={int(verified)} blr_verified=0")
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print("V400_NAND_PARENT_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V400_NAND_PARENT_AUDIT verified=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
