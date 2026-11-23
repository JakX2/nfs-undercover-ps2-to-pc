#!/usr/bin/env python3
"""V386 sanitized audit: next authentic original NAND IPC guest helper."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V386_NAND_NEXT_ENTRY guest=([01]) registered=([01]) masked=([01]) signal=([01]) writer=([01]) cache=([01])$')
TRIAL=re.compile(r'^V386_NAND_NEXT_TRIAL stopped=([01]) next=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    signal_any=writer_any=cache_any=0
    good=True
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries>=16 or entries!=trials:
                good=False;break
            entries+=1
            guest,registered,masked,signal,writer,cache=map(int,e.groups())
            signal_any|=signal;writer_any|=writer;cache_any|=cache
            good=good and bool(guest and registered and masked and signal)
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:
                good=False;break
            trials+=1
            good=good and all(v=='1' for v in t.groups())
    return (
        f'V386_NAND_NEXT_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'signal_any={signal_any} writer_any={writer_any} cache_any={cache_any} '
        f'next_verified={int(bool(good and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V386_NAND_NEXT_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V386_NAND_NEXT_AUDIT verified=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
