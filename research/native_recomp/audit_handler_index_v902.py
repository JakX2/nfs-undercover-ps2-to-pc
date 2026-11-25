#!/usr/bin/env python3
"""Identify the original indexed load after the SI status W1C without publishing private addresses."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v868_handler_suffix import lane
from prepare_owner_status_w1c_v900 import channel_register
from audit_handler_path_v887 import step
from audit_handler_frontier_v896 import region

def inputs(code,channel,status,seed=0,base_reg=None,base_value=0):
    r=tuple(seed^(i*0x1234567&0xffffffff) for i in range(32))
    r=list(r);r[channel[0]]=channel[1]
    if base_reg is not None:r[base_reg]=base_value
    r=tuple(r)
    for i,w in enumerate(code[:11]):
        op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        if i==5:
            rr=list(r);rr[rs]=status;r=tuple(rr)
        elif op==31 and xo in (60,536,124):
            rr=list(r);x,y=r[rs],r[rb]
            rr[ra]=None if x is None or y is None else ((x&~y) if xo==60 else (0 if y&32 else x>>(y&31)) if xo==536 else ~(x|y))&0xffffffff
            r=tuple(rr)
        else:r=step(w,r)
    return r

def address(w,r):
    if w>>26!=31 or (w>>1)&1023 not in (23,55,534,87,119,279,311,343,375,790):raise ValueError('indexed load shape')
    ra=(w>>16)&31;rb=(w>>11)&31
    a=r[ra] if ra else 0;b=r[rb]
    return None if a is None or b is None else (a+b)&0xffffffff

def classify_index(code):
    if len(code)!=12:raise ValueError('prefix extent')
    selector=channel_register(code);w=code[-1]
    candidates=[]
    # First distinguish a static channel table from an inherited pointer.
    for reg in (None,*range(14,32),2,13):
        if reg==selector:continue
        values=[]
        for seed in (0,0x13579bdf):
            for ch in range(4):
                for status in (0,0x08080808,0x0f0f0f0f):
                    base=0x80090000
                    r=inputs(code,(selector,ch),status,seed,reg,base)
                    values.append(address(w,r))
        if None in values:continue
        first=values[:12]
        if values[12:]!=first or any(len(set(first[i:i+3]))!=1 for i in range(0,12,3)):continue
        aa=first[::3];stride=(aa[1]-aa[0])&0xffffffff
        if stride>256 or any(aa[i]!=(aa[0]+i*stride)&0xffffffff for i in range(4)):continue
        if reg is not None:
            rr=inputs(code,(selector,0),0,0,reg,0x800a0000)
            if address(w,rr)!=(aa[0]+0x10000)&0xffffffff:continue
        candidates.append((reg,aa,stride))
    return candidates

def inspect(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf);start=sites[0]+4
    rows=lane(HANDLER,words,start,(52,0,1,((1,7),(1,8),(1,12))))
    code=[rows[start+4*i][0] for i in range(12)]
    if any(rows[start+4*i][1:]!=(0,0) or w>>26 in (16,18,19) for i,w in enumerate(code)):raise ValueError('linear prefix')
    w=code[-1];xo=(w>>1)&1023
    candidates=classify_index(code)
    print(f'V902_INDEX_CLASS opcode_xo={xo} candidates={len(candidates)}')
    for reg,aa,stride in candidates:
        rr=inputs(code,(channel_register(code),0),0,0,reg,0x80090000)
        kind,area,op=region(w,rr)
        print(f'V902_INDEX_PROVENANCE inherited_base={int(reg is not None)} base_class={"none" if reg is None else "sda" if reg in (2,13) else "nonvolatile"} region={area} stride={stride} channel_entries={len(set(aa))}')
    print('V902_INDEX_CENSUS verified=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError):
        print('V902_INDEX_CENSUS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
