#!/usr/bin/env python3
"""Classify return paths after original immediate-transfer predicate and alarm time."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_transfer_callee_v909 import plan
from prepare_owner_transfer_v765 import plan as full_transfer
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_handler_suffix_v728 import suffix,target
from audit_handler_third_v740 import names
from audit_handler_branch_frontier_v907 import frontier
from audit_handler_path_v887 import classify

def describe(root,words,start,elf,label):
    n,b,s,stops=suffix(root,words,start)
    kinds=','.join(names(elf,d) if k==1 and d is not None else str(k) for _,k,_,d in stops)
    print(f'{label} labels={n} loops={b} stores={s} boundaries={len(stops)} next={kinds}')
    return stops

def inspect(dol,elf):
    q,nested,_,_,tails=plan(dol,elf)
    roots,C,D,Q,S,R,edges=full_transfer(dol,elf)
    if C!=nested[1][0]:raise ValueError('immediate identity')
    branch,w=tails[1];code=roots[C]
    if code[(branch-C)//4]!=w or w>>26!=16 or w&3:raise ValueError('branch shape')
    for taken,pc in enumerate((branch+4,target(branch,w))):
        stops=describe(C,code,pc,elf,f'V915_IMMEDIATE_ARM taken={taken}')
        for site,k,o,d in stops:
            if k==1 and d==Q:
                describe(C,code,site+4,elf,f'V915_IMMEDIATE_AFTER_RESTORE taken={taken} ordinal={o}')
    addr=nested[0][0];sizes=parse_functions(elf);words=exact(dol,elf,addr,sizes[addr]//4)
    site=tails[0][0];tail,(i,w)=frontier(addr,words,(site-addr)//4+1)
    print(f'V915_ALARM_AFTER_TIME words={len(tail)} loads={sum(classify(w,(None,)*32)[0]=="load" for w in tail)} stores={sum(classify(w,(None,)*32)[0]=="store" for w in tail)} next_opcode={w>>26} next_name={names(elf,target(addr+4*i,w)) if w>>26==18 and w&3==1 else "local_or_system"}')
    print('V915_RETURN_CENSUS verified=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError):
        print('V915_RETURN_CENSUS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
