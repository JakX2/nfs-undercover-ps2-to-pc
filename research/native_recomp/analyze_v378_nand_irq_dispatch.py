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
    all_valid=True
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries>=16 or entries!=trials:
                all_valid=False
                break
            entries+=1
            this_ok=all(x=='1' for x in e.groups())
            entry_any|=int(this_ok)
            all_valid=all_valid and this_ok
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:
                all_valid=False
                break
            trials+=1
            this_ok=all(x=='1' for x in t.groups())
            trial_any|=int(this_ok)
            all_valid=all_valid and this_ok
    return (
        f'V378_NAND_DISPATCH_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'entry_any={int(bool(entry_any))} trial_any={int(bool(trial_any))} '
        f'dispatch_verified={int(bool(all_valid and entries and entries==trials and entry_any and trial_any))}'
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
