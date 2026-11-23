#!/usr/bin/env python3
"""Fail-closed V397 owner gate for a bounded original guest LR lineage census.

Require the independent V396 owner proof and exactly sixteen V397 original
guest callsite LR observations. This does NOT establish a PPC return, completed
NAND callback, native game boot, or frontend execution. No private code,
register values, or raw log text are exported.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from audit_v396_native_gate import verify as verify_v396
from analyze_v397_nand_callback_lineage import inspect as inspect_v397

RESULT=re.compile(
    r"^V397_NAND_ORIGINS_CENSUS rc=0 kind=zero size_band=[0-3] "
    r"sample_complete=[01] entries=16 trials=16 mask=([1-9]|1[0-5]) "
    r"full_cap_all=([01]) selected_any=([01]) isfs_any=([01]) "
    r"parent_any=([01]) other_any=([01]) same_lr_any=([01]) "
    r"lineage_verified=1 return_verified=0$"
)

def verify(path:Path,rc:int)->bool:
    if rc!=0 or not verify_v396(path,rc):
        return False
    m=RESULT.fullmatch(inspect_v397(path,rc))
    if m is None:
        return False
    mask,full_cap,selected,isfs,parent,other,same=map(int,m.groups())
    if (selected,isfs,parent,other)!=tuple(int(bool(mask&(1<<i))) for i in range(4)):
        return False
    # Either all sixteen trials exhausted the cap or a selected-origin
    # call was actually observed. Neither condition proves a return.
    return bool(full_cap or selected)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_original_log",type=Path)
    p.add_argument("native_exit_code",type=int)
    a=p.parse_args()
    try:passed=verify(a.private_original_log,a.native_exit_code)
    except (OSError,ValueError):passed=False
    print(f"V397_OWNER_RESULT_GATE verified={int(passed)} return_verified=0")
    return 0 if passed else 1

if __name__=="__main__":
    raise SystemExit(main())
