#!/usr/bin/env python3
"""V384 original NAND guest reply-handler first PPCCTRL reader evidence."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(
    r'^V384_NAND_REPLY_READ caller=([01]) irq=([01]) registered=([01]) masked=([01]) advanced=([01])$'
)
TRIAL=re.compile(
    r'^V384_NAND_REPLY_READ_TRIAL reply=([01]) reader=([01]) completed=([01])$'
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
            positive=all(v=='1' for v in e.groups())
            entry_any|=int(positive)
            valid=valid and positive
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:
                valid=False;break
            trials+=1
            positive=all(v=='1' for v in t.groups())
            trial_any|=int(positive)
            valid=valid and positive
    return (
        f'V384_NAND_REPLY_READ_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'entry_any={entry_any} trial_any={trial_any} '
        f'ipc_read_verified={int(bool(valid and entries and entries==trials and entry_any and trial_any))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_native_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_native_log,a.native_exit_code))
    except (OSError,ValueError):
        print('V384_NAND_REPLY_READ_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V384_NAND_REPLY_READ_AUDIT verified=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
