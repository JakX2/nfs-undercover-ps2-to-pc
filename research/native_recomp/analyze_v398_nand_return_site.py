#!/usr/bin/env python3
"""Read-only V398 natural saved-return-PC census; no BLR claims."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers
ENTRY=re.compile(
    r'^V398_NAND_RETURN_PC samples=([0-9]|[1-5][0-9]|6[0-4]) '
    r'site=([01]) mapped=([01]) before_cap=([01]) '
    r'saved_lr_valid=([01]) blr_verified=0$')
TRIAL=re.compile(r'^V398_NAND_RETURN_TRIAL site=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,TRIAL))
    entries=trials=0
    sampled_any=site_any=mapped_any=pre_any=0
    max_samples=0
    last_site=0
    valid=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:
                valid=False
                break
            entries+=1
            samples,site,mapped,pre,lr=map(int,m.groups())
            valid=bool(valid and lr and (not site or samples) and
                       (not mapped or site) and (not pre or site))
            last_site=site
            max_samples=max(max_samples,samples)
            sampled_any|=int(samples>0)
            site_any|=site
            mapped_any|=mapped
            pre_any|=pre
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:
                valid=False
                break
            trials+=1
            site,completed=map(int,m.groups())
            valid=bool(valid and completed and site==last_site)
    complete=bool(not overflow and valid and entries==trials and entries)
    return (
        f'V398_NAND_RETURN_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} max_samples={max_samples} '
        f'sampled_any={sampled_any} site_any={site_any} '
        f'mapped_any={mapped_any} before_cap_any={pre_any} '
        f'witness_verified={int(complete)} blr_verified=0'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V398_NAND_RETURN_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V398_NAND_RETURN_AUDIT verified=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
