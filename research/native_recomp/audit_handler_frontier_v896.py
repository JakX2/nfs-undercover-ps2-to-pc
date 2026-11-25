#!/usr/bin/env python3
"""Redacted original handler and SITransfer nested-boundary census."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v868_handler_suffix import lane
from audit_handler_path_v887 import classify,step,signed
from audit_handler_suffix_v728 import target
from prepare_owner_transfer_callee_v895 import plan
from classify_save_leaf_v683 import inspect_suffix,symbol_evidence
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import names

def region(w,regs):
    kind,area,_,op=classify(w,regs)
    ra=(w>>16)&31;rb=(w>>11)&31
    base=regs[ra] if ra else 0
    a=None
    if kind in ('load','store') and base is not None:
        if 32<=op<=47:a=(base+signed(w))&0xffffffff
        elif op==31 and regs[rb] is not None:a=(base+regs[rb])&0xffffffff
    if a is None:return kind,area,op
    p=(a&0x3fffffff)&~0x00800000
    if 0x0d006400<=p<0x0d006500:
        off=p-0x0d006400
        area={0x30:'si_poll',0x34:'si_control',0x38:'si_status'}.get(off,'si_buffer' if 0x80<=off<0x100 else 'si_other')
    elif 0x80000000<=a<0x81800000:area='mem1_cached'
    elif 0xc0000000<=a<0xc1800000:area='mem1_uncached'
    return kind,area,op

def paths(rows,start,depth,seed=None):
    work=[(start,1,(None,)*32 if seed is None else seed)]
    out=set()
    while work:
        pc,i,regs=work.pop()
        if pc not in rows:raise ValueError('path extent')
        w,o,k=rows[pc];op=w>>26
        if i==depth:
            out.add(region(w,regs));continue
        if k:continue
        r=step(w,regs)
        if op in (16,18):
            dst=target(pc,w)
            if dst<=pc:raise ValueError('backward path')
            work.append((dst,i+1,r))
            if op==18:continue
        work.append((pc+4,i+1,r))
        if len(work)>128:raise ValueError('path count')
    return sorted(out)

def inspect(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf);start=sites[0]+4
    rows=lane(HANDLER,words,start,(52,0,1,((1,7),(1,8),(1,12))))
    for i in range(9,17):
        for kind,area,op in paths(rows,start,i):
            print(f'V896_HANDLER_PATH visit={i} class={kind} region={area} opcode_class={op}')
    q=plan(dol,elf);sizes=parse_functions(elf)
    for ordinal,(site,addr,prefix,w) in zip((5,6),q[-1]):
        pc=addr+4*(len(prefix)-1);op=w>>26
        if op!=18 or w&3!=1:raise ValueError('nested control')
        dst=direct_bl(w,pc);info={'kind':0,'registers':0}
        try:info=inspect_suffix(dol,elf,dst)
        except ValueError:pass
        ev=symbol_evidence(elf,dst)
        print(f'V896_CALLEE_NESTED ordinal={ordinal} named={names(elf,dst)} sized={int(bool(sizes.get(dst)))} save_kind={info["kind"]} registers={info["registers"]} alias={int(bool(ev["zero_func"] or ev["notype"]))}')
    print('V896_FRONTIER_CENSUS verified=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError):
        print('V896_FRONTIER_CENSUS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
