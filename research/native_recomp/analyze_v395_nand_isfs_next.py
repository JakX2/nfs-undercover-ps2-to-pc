#!/usr/bin/env python3
"""V395 sanitized original Wii NAND ISFS callback's first guest call."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V395_NAND_ISFS_NEXT guest=([01]) clear=([01]) masked=([01]) registered=([01]) mapped=([01]) selected=([01]) userdata=([01]) nand=([01])$')
TRIAL=re.compile(r'^V395_NAND_ISFS_TRIAL isfs=([01]) next=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    mapped_any=selected_any=userdata_any=nand_any=0
    valid=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:valid=False;break
            entries+=1
            guest,clear,masked,registered,mapped,selected,userdata,nand=map(int,m.groups())
            valid=valid and bool(guest and clear and masked and registered)
            mapped_any|=mapped;selected_any|=selected;userdata_any|=userdata;nand_any|=nand
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:valid=False;break
            trials+=1
            valid=valid and all(x=='1' for x in m.groups())
    return (
        f'V395_NAND_ISFS_NEXT_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} mapped_any={mapped_any} '
        f'selected_any={selected_any} userdata_any={userdata_any} '
        f'nand_any={nand_any} '
        f'next_verified={int(bool(valid and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (OSError,ValueError):
        print('V395_NAND_ISFS_NEXT_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V395_NAND_ISFS_NEXT_AUDIT verified=1')
    return 0
if __name__=="__main__":raise SystemExit(main())
