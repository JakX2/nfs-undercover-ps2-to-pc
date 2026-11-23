#!/usr/bin/env python3
"""V393 owner-private original NAND post-cache next guest callee census."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
ENTRY=re.compile(r'^V393_NAND_NEXT_CALL guest=([01]) clear=([01]) registered=([01]) masked=([01]) reply=([01]) clearctx=([01]) setctx=([01]) cache=([01]) isfs=([01])$')
TRIAL=re.compile(r'^V393_NAND_NEXT_TRIAL first=([01]) next=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    entries=trials=0
    reply_any=clearctx_any=setctx_any=cache_any=isfs_any=0
    valid=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:valid=False;break
            entries+=1
            guest,clear,reg,masked,reply,clearctx,setctx,cache,isfs=map(int,m.groups())
            valid=valid and bool(guest and clear and reg and masked)
            reply_any|=reply;clearctx_any|=clearctx
            setctx_any|=setctx;cache_any|=cache;isfs_any|=isfs
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:valid=False;break
            trials+=1
            valid=valid and all(v=='1' for v in m.groups())
    return (
        f'V393_NAND_GUEST_NEXT_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} reply_any={reply_any} '
        f'clearctx_any={clearctx_any} setctx_any={setctx_any} '
        f'cache_any={cache_any} isfs_any={isfs_any} '
        f'next_verified={int(bool(valid and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    args=p.parse_args()
    try:print(inspect(args.private_original_log,args.native_exit_code))
    except (OSError,ValueError):
        print('V393_NAND_GUEST_NEXT_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V393_NAND_GUEST_NEXT_AUDIT verified=1')
    return 0
if __name__=="__main__":raise SystemExit(main())
