#!/usr/bin/env python3
"""V382 owner-private original NAND IPC next-call public trace auditor."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(
    r'^V382_NAND_IPC_NEXT guest=([01]) registered=([01]) masked=([01]) advanced=([01]) known=([01]) signal=([01])$'
)
TRIAL=re.compile(r'^V382_NAND_IPC_TRIAL ipc=([01]) next=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    known_any=signal_any=0
    valid=True
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries!=trials or entries>=16:
                valid=False;break
            entries+=1
            guest,reg,masked,advanced,known,signal=map(int,e.groups())
            known_any|=known;signal_any|=signal
            valid=valid and bool(guest and reg and masked and advanced)
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:
                valid=False;break
            trials+=1
            valid=valid and all(x=='1' for x in t.groups())
    return (
        f'V382_NAND_IPC_NEXT_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'known_any={known_any} signal_any={signal_any} '
        f'next_verified={int(bool(valid and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V382_NAND_IPC_NEXT_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V382_NAND_IPC_NEXT_AUDIT verified=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
