#!/usr/bin/env python3
"""Require 16 complete authentic V398 return-site observations, not BLR."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from audit_v397_native_gate import verify as verify_v397
from analyze_v398_nand_return_site import inspect as inspect_v398
RESULT=re.compile(
    r'^V398_NAND_RETURN_CENSUS rc=0 kind=zero size_band=[0-3] '
    r'sample_complete=[01] entries=16 trials=16 '
    r'max_samples=([0-9]|[1-5][0-9]|6[0-4]) '
    r'sampled_any=([01]) site_any=([01]) '
    r'mapped_any=([01]) before_cap_any=([01]) '
    r'witness_verified=1 blr_verified=0$')
def verify(path:Path,rc:int)->bool:
    if rc!=0 or not verify_v397(path,rc):
        return False
    m=RESULT.fullmatch(inspect_v398(path,rc))
    if m is None:
        return False
    samples,sampled,site,mapped,pre=map(int,m.groups())
    return bool((not sampled or samples>0) and
                (not site or sampled) and
                (not mapped or site) and
                (not pre or site))
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:valid=verify(a.private_original_log,a.native_exit_code)
    except (ValueError,OSError):valid=False
    print(f'V398_OWNER_RESULT_GATE verified={int(valid)} blr_verified=0')
    return 0 if valid else 1
if __name__=='__main__':raise SystemExit(main())
