#!/usr/bin/env python3
"""Bounded V401 original PPC guest linksite opcode class census; no opcode leak."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from analyze_v398_nand_return_site import ENTRY as PREVIOUS
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers
ENTRY=re.compile(r'^V401_NAND_CALLSITE mapped=([01]) kind=([0-5]) direct_match=([01]) selected_site=([01]) blr_verified=0$')
TRIAL=re.compile(r'^V401_NAND_CALLSITE_TRIAL kind=([0-5]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(PREVIOUS,ENTRY,TRIAL))
    counts=[0]*6
    entries=trials=matched=site_count=0
    phase=0
    saved_site=last_kind=0
    good=True
    for line in lines:
        m=PREVIOUS.fullmatch(line)
        if m:
            if phase!=0 or entries>=16:
                good=False
                break
            samples,saved_site,saved_mapped,pre,valid_lr=map(int,m.groups())
            good=good and bool(valid_lr and (not saved_site or samples) and
                                (not saved_mapped or saved_site))
            phase=1
            continue
        m=ENTRY.fullmatch(line)
        if m:
            if phase!=1 or entries>=16:
                good=False
                break
            mapped,kind,direct,site=map(int,m.groups())
            good=good and site==saved_site and (mapped==int(kind!=0))
            good=good and (not mapped or site)
            good=good and (not direct or kind in (1,2))
            counts[kind]+=1
            entries+=1
            matched+=direct
            site_count+=site
            last_kind=kind
            phase=2
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if phase!=2 or trials>=16:
                good=False
                break
            kind,completed=map(int,m.groups())
            good=good and bool(completed and kind==last_kind)
            trials+=1
            phase=0
    verified=bool(not overflow and good and phase==0 and entries==trials and entries)
    return (
        f"V401_NAND_CALLSITE_CENSUS rc={rc} kind={category(rc)} "
        f"size_band={size_band(size)} sample_complete={int(size<=WINDOW)} "
        f"entries={entries} trials={trials} "
        + " ".join(f"kind{i}={counts[i]}" for i in range(6))
        + f" site_trials={site_count} direct_match_trials={matched} "
        f"classified={int(verified)} blr_verified=0"
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print("V401_NAND_CALLSITE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V401_NAND_CALLSITE_AUDIT verified=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
