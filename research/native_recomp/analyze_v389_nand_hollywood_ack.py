#!/usr/bin/env python3
"""V389 authenticated guest Hollywood ACK bounded public-only evidence."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V389_NAND_FLAG_ACK before=([01]) wrote=([01]) cleared=([01]) down=([01]) y1=([01]) guest=([01]) registered=([01])$')
TRIAL=re.compile(r'^V389_NAND_FLAG_TRIAL y1=([01]) flag=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    valid=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries>=16 or entries!=trials:valid=False;break
            entries+=1
            valid=valid and all(v=='1' for v in m.groups())
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:valid=False;break
            trials+=1
            valid=valid and all(v=='1' for v in t.groups())
    return (
        f'V389_NAND_FLAG_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'flag_ack_verified={int(bool(valid and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_log,a.native_exit_code))
    except (OSError,ValueError):
        print('V389_NAND_FLAG_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V389_NAND_FLAG_AUDIT verified=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
