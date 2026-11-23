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
    # Bit order: entry guest,clear,masked,registered,mapped,selected,userdata,nand.
    # Trial bit order: isfs,next,completed. These preserve no addresses,
    # register words, response values, names, or other owner-only content.
    entry_or=0
    entry_and=0xff
    trial_or=0
    trial_and=0x07
    first_bad=0
    valid=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:valid=False;break
            entries+=1
            bits=tuple(map(int,m.groups()))
            guest,clear,masked,registered,mapped,selected,userdata,nand=bits
            mask=sum(bit<<i for i,bit in enumerate(bits))
            entry_or|=mask
            entry_and&=mask
            if mask!=0xff and not first_bad:first_bad=entries
            valid=valid and bool(guest and clear and masked and registered)
            mapped_any|=mapped;selected_any|=selected;userdata_any|=userdata;nand_any|=nand
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:valid=False;break
            trials+=1
            bits=tuple(map(int,m.groups()))
            mask=sum(bit<<i for i,bit in enumerate(bits))
            trial_or|=mask
            trial_and&=mask
            if mask!=0x07 and not first_bad:first_bad=trials
            valid=valid and all(bits)
    return (
        f'V395_NAND_ISFS_NEXT_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} mapped_any={mapped_any} '
        f'selected_any={selected_any} userdata_any={userdata_any} '
        f'nand_any={nand_any} '
        f'next_verified={int(bool(valid and entries and entries==trials))}'
        '\n'
        f'V395_NAND_FIELD_CENSUS entries={entries} trials={trials} '
        f'entry_any_mask={entry_or:02X} entry_all_mask={entry_and if entries else 0:02X} '
        f'trial_any_mask={trial_or:01X} trial_all_mask={trial_and if trials else 0:01X} '
        f'first_bad={first_bad} order_ok={int(bool(valid and entries==trials))}'
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
