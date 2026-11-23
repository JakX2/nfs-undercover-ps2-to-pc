#!/usr/bin/env python3
"""V392 bounded sanitized original NAND post-cache guest-call evidence."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
from scan_original_guest_markers import scan_original_guest_markers
ENTRY=re.compile(r'^V392_NAND_POST_CACHE_EVENT kind=([12]) verified=([01]) owner=([01]) cache=([01]) context=([01]) callback=([01]) bounded=([01]) caches=([0-9]|1[0-9]|2[0-4])$')
TRIAL=re.compile(r'^V392_NAND_POST_CACHE_TRIAL kind=([12]) stopped=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,TRIAL))
    entries=trials=0
    owner_any=bounded_any=context_any=callback_any=cache_any=0
    valid=True
    last=0
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:valid=False;break
            entries+=1
            kind,passed,owner,cache,context,callback,bounded,caches=map(int,m.groups())
            valid=valid and bool(passed and (kind==1)==bool(owner and not cache) and
                                 (kind==2)==bool(bounded) and
                                 caches<=24 and not(bounded and owner and not cache))
            last=kind
            owner_any|=owner;bounded_any|=bounded
            context_any|=context;callback_any|=callback;cache_any|=int(caches>0 or cache)
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:valid=False;break
            trials+=1
            kind,stopped,completed=map(int,m.groups())
            valid=valid and bool(kind==last and stopped and completed)
    return (
        f'V392_NAND_POST_CACHE_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} owner_any={owner_any} '
        f'bounded_any={bounded_any} cache_any={cache_any} '
        f'context_any={context_any} callback_any={callback_any} '
        f'next_verified={int(bool(not overflow and valid and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V392_NAND_POST_CACHE_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V392_NAND_POST_CACHE_AUDIT verified=1')
    return 0
if __name__=="__main__":raise SystemExit(main())
