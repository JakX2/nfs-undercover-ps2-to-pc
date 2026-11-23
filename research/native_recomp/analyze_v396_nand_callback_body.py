#!/usr/bin/env python3
"""V396 original-free bounded real ISFS-selected callback-body call census."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers
ENTRY=re.compile(r'^V396_NAND_CB_BODY kind=([12]) verified=([01]) owned=([01]) clear=([01]) masked=([01]) registered=([01]) cache=([01]) context=([01]) nand=([01]) bounded=([01])$')
TRIAL=re.compile(r'^V396_NAND_CB_TRIAL kind=([12]) stopped=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,TRIAL))
    entries=trials=0
    owner_any=cap_any=cache_any=context_any=nand_any=0
    state_any_mask=0
    state_all_mask=7
    all_good=True;last=0
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:all_good=False;break
            entries+=1
            kind,verified,owned,clear,masked,registered,cache,context,nand,bound=map(int,m.groups())
            state_mask=clear|(masked<<1)|(registered<<2)
            state_any_mask|=state_mask
            state_all_mask&=state_mask
            all_good=all_good and bool(verified and
                       (kind==1)==bool(owned) and (kind==2)==bool(bound))
            last=kind
            owner_any|=owned;cap_any|=bound;cache_any|=cache
            context_any|=context;nand_any|=nand
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:all_good=False;break
            trials+=1
            kind,stopped,completed=map(int,m.groups())
            all_good=all_good and bool(kind==last and stopped and completed)
    return (
        f'V396_NAND_CB_BODY_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'owner_any={owner_any} cap_any={cap_any} '
        f'cache_any={cache_any} context_any={context_any} nand_any={nand_any} '
        f'state_any_mask={state_any_mask} '
        f'state_all_mask={state_all_mask if entries else 0} '
        f'next_verified={int(bool(not overflow and all_good and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V396_NAND_CB_BODY_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V396_NAND_CB_BODY_AUDIT verified=1')
    return 0
if __name__=="__main__":raise SystemExit(main())
