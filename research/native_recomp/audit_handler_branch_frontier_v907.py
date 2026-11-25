#!/usr/bin/env python3
"""Redacted dependency census after the verified original conditional branches."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v868_handler_suffix import lane
from prepare_owner_status_w1c_v906 import plan as branch_plan
from prepare_owner_transfer_callee_v905 import plan as transfer_plan
from audit_handler_suffix_v728 import target
from audit_handler_third_v740 import names
from audit_handler_path_v887 import classify,step
from make_private_elf_symbol_map import parse_functions

def frontier(root,code,start,limit=32):
    result=[]
    for i in range(start,min(len(code),start+limit)):
        w=code[i];op=w>>26;xo=(w>>1)&1023
        if op in (16,17,18,19) or op==31 and xo==146:
            return result,(i,w)
        result.append(w)
    raise ValueError('frontier bound')

def counts(words):
    kinds={}
    regs=(None,)*32
    for w in words:
        kind,area,*_=classify(w,regs)
        kinds[kind]=kinds.get(kind,0)+1
        regs=step(w,regs)
    return ' '.join(f'{k}={v}' for k,v in sorted(kinds.items()))

def describe(elf,root,code,start,tag):
    words,(i,w)=frontier(root,code,start)
    pc=root+4*i;op=w>>26
    name=names(elf,target(pc,w)) if op==18 and w&3==1 else 'local_or_system'
    print(f'{tag} words={len(words)} next_opcode={op} next_name={name} '+counts(words))

def inspect(dol,elf):
    start,code,_,_=branch_plan(dol,elf)
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf)
    if start!=sites[0]+4:raise ValueError('handler resume')
    for taken,pc in enumerate((start+56,target(start+52,code[13]))):
        describe(elf,HANDLER,handler,(pc-HANDLER)//4,f'V907_HANDLER_ARM taken={taken}')
    q,nested,_,stops=transfer_plan(dol,elf);sizes=parse_functions(elf)
    for ordinal,(addr,_,_),(site,_,_,_) in zip((5,6),nested,stops):
        code=exact(dol,elf,addr,sizes[addr]//4)
        describe(elf,addr,code,(site-addr)//4+1,f'V907_CALLEE_ARM ordinal={ordinal}')
    print('V907_FRONTIER verified=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError):
        print('V907_FRONTIER verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
