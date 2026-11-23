#!/usr/bin/env python3
"""V391 public-only bounded original NAND post-ACK guest-call census."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V391_NAND_POST_ACK_EVENT kind=([12]) verified=([01]) owner=([01]) cache=([01]) context=([01]) callback=([01]) cap=([01])$')
TRIAL=re.compile(r'^V391_NAND_POST_ACK_TRIAL kind=([12]) stopped=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    owner_any=cap_any=cache_any=context_any=callback_any=0
    valid=True
    last_kind=0
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:valid=False;break
            entries+=1
            kind,verified,owner,cache,context,callback,cap=map(int,m.groups())
            valid=valid and bool(verified and (kind==1)==bool(owner) and
                                  (kind==2)==bool(cap) and not(owner and cap))
            last_kind=kind
            owner_any|=owner;cap_any|=cap;cache_any|=cache
            context_any|=context;callback_any|=callback
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:valid=False;break
            trials+=1
            kind,stopped,completed=map(int,m.groups())
            valid=valid and bool(kind==last_kind and stopped and completed)
    return (
        f'V391_NAND_POST_ACK_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} '
        f'owner_any={owner_any} cap_any={cap_any} cache_any={cache_any} '
        f'context_any={context_any} callback_any={callback_any} '
        f'next_verified={int(bool(valid and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V391_NAND_POST_ACK_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V391_NAND_POST_ACK_AUDIT verified=1')
    return 0
if __name__=="__main__":raise SystemExit(main())
