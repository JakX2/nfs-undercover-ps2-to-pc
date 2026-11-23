#!/usr/bin/env python3
"""V381 bounded sanitized evidence for original registered NAND Y1 IPC entry."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V381_NAND_IPC_ENTRY registered=([01]) context=([01]) abi=([01]) y1=([01]) masked=([01]) advanced=([01])$')
TRIAL=re.compile(r'^V381_NAND_IPC_TRIAL scheduler=([01]) ipc=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    entry_any=trial_any=0
    good=True
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries>=16 or entries!=trials:
                good=False;break
            entries+=1
            passed=all(v=='1' for v in e.groups())
            entry_any|=int(passed)
            good=good and passed
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:
                good=False;break
            trials+=1
            passed=all(v=='1' for v in t.groups())
            trial_any|=int(passed)
            good=good and passed
    verified=int(bool(good and entries and entries==trials and entry_any and trial_any))
    return (
        f'V381_NAND_IPC_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'entry_any={int(bool(entry_any))} trial_any={int(bool(trial_any))} '
        f'ipc_verified={verified}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_native_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_native_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V381_NAND_IPC_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V381_NAND_IPC_AUDIT verified=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
