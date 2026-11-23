#!/usr/bin/env python3
"""V403 fail-closed 16-trial authenticated CTR/SP/LR/opcode-class owner gate."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from audit_v401_native_gate import verify as verify_v401
from analyze_v403_nand_call_provenance import inspect

COUNT=r'([0-9]|1[0-6])'
RESULT=re.compile(
    r'^V403_NAND_CALL_PROVENANCE_CENSUS rc=0 kind=zero size_band=[0-3] '
    r'sample_complete=[01] entries=16 trials=16 '
    + " ".join(f"family{i}={COUNT}" for i in range(9))
    + f" ctr_trials={COUNT} sp_trials={COUNT} lr_trials={COUNT} "
    + f"site_trials={COUNT} classified=1 blr_verified=0$"
)

def verify(path:Path,rc:int)->tuple[bool,int,int,int]:
    good401,_,_=verify_v401(path,rc)
    if rc!=0 or not good401:
        return False,0,0,0
    m=RESULT.fullmatch(inspect(path,rc))
    if m is None:
        return False,0,0,0
    *families,ctr,sp,lr,sites=map(int,m.groups())
    good=(sum(families)==16 and sp<=sites and lr<=sites)
    return bool(good),int(good and ctr==16),int(good and sp==16),int(good and lr==16)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:good,ctr,sp,lr=verify(a.private_original_log,a.native_exit_code)
    except (ValueError,OSError):good,ctr,sp,lr=False,0,0,0
    print(f"V403_OWNER_RESULT_GATE verified={int(good)} "
          f"ctr_all={ctr} sp_all={sp} lr_all={lr} blr_verified=0")
    return 0 if good else 1

if __name__=="__main__":
    raise SystemExit(main())
