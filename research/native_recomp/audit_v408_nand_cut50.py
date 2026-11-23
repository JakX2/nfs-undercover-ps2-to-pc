#!/usr/bin/env python3
"""V408 strict 16/16 owner-original 50-call evidence gate, diagnostic only."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from analyze_v408_nand_cut50 import inspect

STRICT=re.compile(r'^V408_NAND_CUT50_CENSUS rc=0 kind=zero size_band=[0-3] '
                  r'sample_complete=[01] entries=16 trials=16 max_calls=50 '
                  r'owner_trials=0 cap50_trials=16 '
                  r'selected_return_trials=16 parent_return_trials=16 '
                  r'full_progress=1 boot_verified=0$')
def verify(path:Path,rc:int)->bool:
    return rc==0 and STRICT.fullmatch(inspect(path,rc)) is not None

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original_owner_private_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:passed=verify(a.original_owner_private_log,a.native_exit_code)
    except (ValueError,OSError):passed=False
    print(f'V408_OWNER_RESULT_GATE verified={int(passed)} boot_verified=0')
    # Candidate is distinct from V403/V402 historical acceptance gates.
    return 0
if __name__=='__main__':raise SystemExit(main())
