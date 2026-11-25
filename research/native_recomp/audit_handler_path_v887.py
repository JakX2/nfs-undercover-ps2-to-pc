#!/usr/bin/env python3
"""Owner-only branch path census for the V876 sixth-visit refusal."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v868_handler_suffix import lane
from audit_handler_suffix_v728 import target

def signed(w):return ((w&0xffff)^0x8000)-0x8000
def classify(w,regs):
    op=w>>26;xo=(w>>1)&1023;ra=(w>>16)&31;rb=(w>>11)&31
    base=regs[ra] if ra else 0
    kind='integer';addr=None
    if 32<=op<=47:
        kind='store' if op in (36,37,38,39,44,45,47) else 'load'
        if base is not None:addr=(base+signed(w))&0xffffffff
    elif op==31 and xo in (23,55,534,87,119,279,311,343,375,790,151,183,215,247,407,439,662,918):
        kind='store' if xo in (151,183,215,247,407,439,662,918) else 'load'
        if base is not None and regs[rb] is not None:addr=(base+regs[rb])&0xffffffff
    elif op==31 and xo in (20,150,533,597,661,725,535,567,599,631,663,695,727,759,983,54,86,246,278,470,982,1014):kind='unsupported_x'
    elif op>=48 or op==4:kind='unsupported_fp'
    elif op in (16,18):kind='branch'
    region='unknown'
    if addr is not None:
        phys=(addr&0x3fffffff)&~0x00800000
        region='si' if 0x0d006400<=phys<0x0d006500 else 'mem1' if 0x80000000<=addr<0x81800000 else 'other'
    return kind,region,ra in (1,2,13),op

def step(w,regs):
    op=w>>26;rd=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31;xo=(w>>1)&1023
    r=list(regs);base=regs[ra] if ra else 0
    if op in (14,15):r[rd]=None if base is None else (base+(signed(w)<<(16 if op==15 else 0)))&0xffffffff
    elif op in (24,25):r[ra]=None if regs[rd] is None else regs[rd]|((w&0xffff)<<(16 if op==25 else 0))
    elif op==31 and xo==444:r[ra]=None if regs[rd] is None or regs[rb] is None else regs[rd]|regs[rb]
    elif op in (10,11,16,18,36,38,44):pass
    else:r=[None]*32
    return tuple(r)

def paths(rows,start,depth=6):
    work=[(start,0,(None,)*32)];out=set()
    while work:
        pc,i,regs=work.pop()
        if pc not in rows:raise ValueError('path extent')
        w,o,k=rows[pc];op=w>>26
        if i+1==depth:
            out.add(classify(w,regs));continue
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
    for depth in range(1,9):
        for k,region,base,op in paths(rows,start,depth):
            print(f'V887_HANDLER_PATH visit={depth} class={k} region={region} special_base={int(base)} opcode_class={op}')
    print('V887_HANDLER_CENSUS verified=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError):print('V887_HANDLER_CENSUS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
