#!/usr/bin/env python3
"""Original-free V400 owner gate for natural ISFS-to-IPC parent continuation."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from audit_v399_native_gate import verify as verify_v399
from analyze_v400_nand_parent_resume import inspect
RESULT=re.compile(
    r'^V400_NAND_PARENT_CENSUS rc=0 kind=zero size_band=[0-3] '
    r'sample_complete=[01] entries=16 trials=16 '
    r'site_trials=([0-9]|1[0-6]) mapped_trials=([0-9]|1[0-6]) '
    r'linked_trials=([0-9]|1[0-6]) selected_first_trials=([0-9]|1[0-6]) '
    r'parent_after_trials=([0-9]|1[0-6]) ordered_trials=([0-9]|1[0-6]) '
    r'lineage_verified=1 blr_verified=0$')
def verify(path:Path,rc:int)->tuple[bool,int,int]:
    previous,_,_=verify_v399(path,rc)
    if rc!=0 or not previous:
        return False,0,0
    m=RESULT.fullmatch(inspect(path,rc))
    if not m:
        return False,0,0
    site,mapped,linked,first,parent,ordered=map(int,m.groups())
    valid=(ordered<=parent and parent<=mapped and
           first<=site and first<=mapped and
           mapped<=site and linked<=site)
    return bool(valid),int(valid and ordered==16),int(valid and linked==16)
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:good,ordered,linked=verify(a.private_original_log,a.native_exit_code)
    except (ValueError,OSError):good,ordered,linked=False,0,0
    print(f"V400_OWNER_RESULT_GATE verified={int(good)} "
          f"ordered_all={ordered} link_all={linked} blr_verified=0")
    return 0 if good else 1
if __name__=="__main__":raise SystemExit(main())
