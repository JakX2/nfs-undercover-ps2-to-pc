#!/usr/bin/env python3
"""V378 sanitize original NAND handler to real guest dispatcher checkpoint."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V378_NAND_DISPATCH_ENTRY route=([01]) regs=([01]) status=([01]) masked=([01]) y1=([01]) advanced=([01])$')
TRIAL=re.compile(r'^V378_NAND_DISPATCH_TRIAL handler=([01]) dispatch=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    entry_any=trial_any=0
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries>=16:break
            entries+=1
            entry_any|=int(all(x=='1' for x in e.groups()))
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:break
            trials+=1
            trial_any|=int(all(x=='1' for x in t.groups()))
    return (
        f'V378_NAND_DISPATCH_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'entry_any={int(bool(entry_any))} trial_any={int(bool(trial_any))} '
        f'dispatch_verified={int(bool(entries and entries==trials and entry_any and trial_any))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit',type=int)
    args=p.parse_args()
    try:print(inspect(args.private_original_log,args.native_exit))
    except (ValueError,OSError):
        print('V378_NAND_DISPATCH_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V378_NAND_DISPATCH_AUDIT verified=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
