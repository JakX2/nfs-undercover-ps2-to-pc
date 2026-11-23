#!/usr/bin/env python3
"""V404 original-guest 96-call owner outcome: explicit 16-trial evidence gate.

Unlike the baseline V403 owner gate, this is a diagnostic experimental
candidate; a zero result is not boot progress and cannot override V402
48-call evidence. Never export guest code or private registers.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from analyze_v404_nand_extended import inspect

SUCCESS=re.compile(
    r'^V404_NAND_EXTENDED_CENSUS rc=0 kind=zero size_band=[0-3] '
    r'sample_complete=[01] entries=16 trials=16 max_calls=96 '
    r'owner_trials=0 cap96_trials=16 '
    r'selected_return_trials=16 parent_return_trials=16 '
    r'full_progress=1 boot_verified=0$')

def verify(path:Path,rc:int)->bool:
    return rc==0 and SUCCESS.fullmatch(inspect(path,rc)) is not None

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:
        valid=verify(a.private_original_log,a.native_exit_code)
    except (ValueError,OSError):
        valid=False
    print(f'V404_OWNER_RESULT_GATE verified={int(valid)} boot_verified=0')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
