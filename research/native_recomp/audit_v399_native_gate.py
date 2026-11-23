#!/usr/bin/env python3
"""V399 fail-closed owner gate for 16 ordered guest resume/caller records."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from audit_v398_native_gate import verify as verify_v398
from analyze_v399_nand_return_order import inspect
RESULT=re.compile(
    r'^V399_NAND_RETURN_CENSUS rc=0 kind=zero size_band=[0-3] '
    r'sample_complete=[01] entries=16 trials=16 '
    r'site_trials=([0-9]|1[0-6]) mapped_trials=([0-9]|1[0-6]) '
    r'bctrl_trials=([0-9]|1[0-6]) isfs_after_trials=([0-9]|1[0-6]) '
    r'parent_after_trials=([0-9]|1[0-6]) ordered_trials=([0-9]|1[0-6]) '
    r'lineage_verified=1 blr_verified=0$')
def verify(path:Path,rc:int)->tuple[bool,int,int]:
    if rc!=0 or not verify_v398(path,rc):
        return False,0,0
    m=RESULT.fullmatch(inspect(path,rc))
    if not m:
        return False,0,0
    site,mapped,bctrl,isfs,parent,ordered=map(int,m.groups())
    valid=(ordered<=isfs and isfs<=mapped and mapped<=site and
           parent<=mapped and bctrl<=site)
    return bool(valid),int(valid and ordered==16),int(valid and bctrl==16)
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:valid,ordered,bctrl=verify(a.private_original_log,a.native_exit_code)
    except (ValueError,OSError):valid,ordered,bctrl=False,0,0
    print(f"V399_OWNER_RESULT_GATE verified={int(valid)} "
          f"ordered_all={ordered} bctrl_all={bctrl} blr_verified=0")
    return 0 if valid else 1
if __name__=="__main__":raise SystemExit(main())
