#!/usr/bin/env python3
"""V403: original-free selected-callee CTR, LR/SP and nonlink opcode census."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from analyze_v401_nand_callsite import ENTRY as V401_ENTRY
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers

ENTRY=re.compile(
    r'^V403_NAND_CALL_PROVENANCE ctr=([01]) sp=([01]) lr=([01]) '
    r'family=([0-8]) v401_kind=([0-5]) selected_site=([01]) blr_verified=0$'
)
TRIAL=re.compile(r'^V403_NAND_CALL_PROVENANCE_TRIAL family=([0-8]) complete=([01])$')

def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(V401_ENTRY,ENTRY,TRIAL))
    n=trials=phase=last_family=0
    families=[0]*9
    ctr=stack=lr=sites=0
    good=True
    prior_kind=prior_site=0
    for line in lines:
        m=V401_ENTRY.fullmatch(line)
        if m:
            if phase!=0 or n>=16:
                good=False
                break
            mapped,prior_kind,direct,prior_site=map(int,m.groups())
            good=good and bool((mapped==int(prior_kind!=0)) and
                               (not mapped or prior_site) and
                               (not direct or prior_kind in (1,2)))
            phase=1
            continue
        m=ENTRY.fullmatch(line)
        if m:
            if phase!=1 or n>=16:
                good=False
                break
            c,sp,lrf,fam,kind,site=map(int,m.groups())
            good=good and bool(kind==prior_kind and site==prior_site and
                (fam!=0)==(kind==5) and
                (not sp or site) and (not lrf or site))
            n+=1
            ctr+=c
            stack+=sp
            lr+=lrf
            sites+=site
            families[fam]+=1
            last_family=fam
            phase=2
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if phase!=2 or trials>=16:
                good=False
                break
            family,complete=map(int,m.groups())
            good=good and bool(family==last_family and complete)
            trials+=1
            phase=0
    verified=bool(not overflow and good and phase==0 and
                  n==trials and n>0 and sum(families)==n)
    return (
        f"V403_NAND_CALL_PROVENANCE_CENSUS rc={rc} kind={category(rc)} "
        f"size_band={size_band(size)} sample_complete={int(size<=WINDOW)} "
        f"entries={n} trials={trials} "
        + " ".join(f"family{i}={families[i]}" for i in range(9))
        + f" ctr_trials={ctr} sp_trials={stack} lr_trials={lr} "
        f"site_trials={sites} classified={int(verified)} blr_verified=0"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print("V403_NAND_CALL_PROVENANCE_AUDIT inspected=0",file=sys.stderr)
        return 1
    print("V403_NAND_CALL_PROVENANCE_AUDIT inspected=1")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
