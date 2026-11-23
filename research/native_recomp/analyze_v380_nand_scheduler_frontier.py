#!/usr/bin/env python3
"""V380 privacy-safe census of original NAND Y1 IRQ scheduler handoff."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

ENTRY=re.compile(r'^V380_NAND_SCHED_ENTRY guest=([01]) irq=([01]) masked=([01]) advanced=([01]) sda=([01])$')
TRIAL=re.compile(r'^V380_NAND_SCHED_TRIAL time=([01]) scheduler=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    entry_any=trial_any=0
    valid=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:
                valid=False
                break
            entries+=1
            passed=all(x=='1' for x in m.groups())
            entry_any|=int(passed)
            valid=valid and passed
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:
                valid=False
                break
            trials+=1
            passed=all(x=='1' for x in m.groups())
            trial_any|=int(passed)
            valid=valid and passed
    verified=int(bool(valid and entries and entries==trials and entry_any and trial_any))
    return (
        f'V380_NAND_SCHED_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'entry_any={int(bool(entry_any))} trial_any={int(bool(trial_any))} '
        f'scheduler_verified={verified}'
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V380_NAND_SCHED_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V380_NAND_SCHED_AUDIT verified=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
