#!/usr/bin/env python3
"""Authenticate known leaf geometry independently of the post-ACK runtime."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact,DISABLE,TIME,RESTORE
from make_private_elf_symbol_map import parse_functions
from si_nested_geometry_v693 import nested_plan
from prepare_v668_si_ack import shape
def plan(dol,elf):
    _,root,_,_,words=nested_plan(dol,elf);_,calls,indirect=shape(root,words)
    if indirect or tuple(t for _,t in calls)!=(DISABLE,TIME,RESTORE):raise ValueError('leaf order')
    sizes=parse_functions(elf);out=[]
    for kind,((site,target),n) in enumerate(zip(calls,(5,6,9)),1):
        if sizes.get(target)!=4*n:raise ValueError('leaf extent')
        code=exact(dol,elf,target,n);mt=[i for i,w in enumerate(code) if w>>26==31 and (w>>1)&1023==146]
        if code.count(0x4e800020)!=1 or len(mt)!=(0 if kind==2 else 1) or any(w&1 and (w>>26 in (16,18) or w>>26==19 and (w>>1)&1023 in (16,528)) for w in code):raise ValueError('leaf shape')
        out.append((site,target,target+4*n,words[(site-root)//4],kind,code,mt))
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        rows=plan(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError):print('V703_OS_LEAF_GEOMETRY verified=0');return 1
    print(f'V703_OS_LEAF_GEOMETRY verified=1 roots={len(rows)} words={sum(len(x[5]) for x in rows)} mtmsr={sum(len(x[6]) for x in rows)} execution=0');return 0
if __name__=='__main__':raise SystemExit(main())
