#!/usr/bin/env python3
"""V379 public-only original NAND Y1 dispatcher to Wii OSGetTime census."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(
    r'^V379_NAND_TIME_ENTRY guest=([01]) signal=([01]) masked=([01]) progressed=([01]) resume=([01])$'
)
TRIAL=re.compile(
    r'^V379_NAND_TIME_TRIAL dispatch=([01]) time=([01]) completed=([01])$'
)
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    entry_any=trial_any=0
    valid=True
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries!=trials or entries>=16:
                valid=False;break
            entries+=1
            passed=all(x=='1' for x in e.groups())
            entry_any|=int(passed)
            valid=valid and passed
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:
                valid=False;break
            trials+=1
            passed=all(x=='1' for x in t.groups())
            trial_any|=int(passed)
            valid=valid and passed
    verified=int(bool(valid and entries and entries==trials and
                      entry_any and trial_any))
    return (
        f'V379_NAND_TIME_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'entry_any={int(bool(entry_any))} trial_any={int(bool(trial_any))} '
        f'guest_time_verified={verified}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    args=p.parse_args()
    try:print(inspect(args.private_original_log,args.native_exit_code))
    except (OSError,ValueError):
        print('V379_NAND_TIME_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V379_NAND_TIME_AUDIT verified=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
