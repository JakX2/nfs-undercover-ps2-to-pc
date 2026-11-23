#!/usr/bin/env python3
"""Independent V401 authenticated guest linksite classification owner gate."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from audit_v400_native_gate import verify as verify_v400
from analyze_v401_nand_callsite import inspect
COUNT=r'([0-9]|1[0-6])'
RESULT=re.compile(
    r'^V401_NAND_CALLSITE_CENSUS rc=0 kind=zero size_band=[0-3] '
    r'sample_complete=[01] entries=16 trials=16 '
    + " ".join(f"kind{i}={COUNT}" for i in range(6))
    + f" site_trials={COUNT} direct_match_trials={COUNT} "
    + r'classified=1 blr_verified=0$'
)
def verify(path:Path,rc:int)->tuple[bool,int,int]:
    prior,_,_=verify_v400(path,rc)
    if rc!=0 or not prior:
        return False,0,0
    m=RESULT.fullmatch(inspect(path,rc))
    if m is None:
        return False,0,0
    *kinds,site,matched=map(int,m.groups())
    good=(sum(kinds)==16 and
          matched<=kinds[1]+kinds[2] and
          site>=16-kinds[0])
    return bool(good),int(good and matched==16),int(good and kinds[5]==16)
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:good,direct,other=verify(a.private_original_log,a.native_exit_code)
    except (ValueError,OSError):good,direct,other=False,0,0
    print(f"V401_OWNER_RESULT_GATE verified={int(good)} "
          f"direct_all={direct} other_all={other} blr_verified=0")
    return 0 if good else 1
if __name__=="__main__":raise SystemExit(main())
