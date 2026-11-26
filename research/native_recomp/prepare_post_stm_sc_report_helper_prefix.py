#!/usr/bin/env python3
"""Authenticate the first original diagnostic-helper call corridor."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_report_fixture import plan as prefix_plan
from prepare_post_stm_sc_report_helper import census
from prepare_stm_final_return import spr
from prepare_v419_full_start import MAX_DOL,direct_bl,EXPECTED_GPRS
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import category

def prefix(root,words,*,details=False):
    edges,reach,_,first,_,_,_,_=census(root,words)
    if first not in edges:raise ValueError('SC report helper first call')
    n=(first-root)//4+1
    if not 4<=n<=32:raise ValueError('SC report helper prefix extent')
    gp=[('reg',r) for r in range(32)];gp[1]=('stack',0)
    mem={};frame=0;stores=loads=0
    def add(v,imm):
        if v[0] in ('stack','const'):return (v[0],v[1]+imm if v[0]=='stack' else (v[1]+imm)&0xffffffff)
        if not imm:return v
        return ('computed',0)
    def write(at,v):
        if not frame or at%4 or not -frame<=at<=4 or at in mem:
            raise ValueError('SC report helper stack slot')
        mem[at]=v
    for i,w in enumerate(words[:n]):
        op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        imm=((w&0xffff)^0x8000)-0x8000
        if i==n-1:
            if direct_bl(w,first)!=edges[first]:raise ValueError('SC report helper first call')
            break
        if op==37 and rs==ra==1:
            if frame or not -256<=imm<=-8 or imm%8:raise ValueError('SC report helper frame')
            frame=-imm;write(imm,gp[1]);gp[1]=('stack',imm);stores+=1
        elif op==36 and ra==1:
            write(gp[1][1]+imm,gp[rs]);stores+=1
        elif op==47 and ra==1:
            for j in range(rs,32):write(gp[1][1]+imm+4*(j-rs),gp[j])
            stores+=1
        elif op==32 and ra==1 and rs!=1:
            at=gp[1][1]+imm
            if at not in mem:raise ValueError('SC report helper stack load')
            gp[rs]=mem[at];loads+=1
        elif op==31 and xo==339 and spr(w)==8 and rs!=1:gp[rs]=('lr',0)
        elif op in (14,15) and rs!=1:
            gp[rs]=add(gp[ra] if ra else ('const',0),imm<<(16 if op==15 else 0))
        elif op==31 and xo==444 and rs==rb and not w&1 and ra!=1:gp[ra]=gp[rs]
        elif op in (24,25) and ra!=1:
            v=gp[rs];nimm=(w&0xffff)<<(16 if op==25 else 0)
            gp[ra]=('const',v[1]|nimm) if v[0]=='const' else v if not nimm else ('computed',0)
        else:
            kind=category(w)
            raise ValueError(f'SC report helper prefix opcode {kind} {i+1}')
    if not frame or gp[1]!=('stack',-frame) or mem.get(-frame)!=('stack',0) or mem.get(4)!=('lr',0):
        raise ValueError('SC report helper frame')
    saved={at:v[1] for at,v in mem.items() if v[0]=='reg' and 14<=v[1]<=31}
    if len(set(saved.values()))!=len(saved) or any(gp[r]!=('reg',r) and r not in saved.values() for r in range(14,32)):
        raise ValueError('SC report helper nonvolatile')
    if details:return tuple(gp),dict(mem),frame,edges[first]
    return n,frame,stores,loads,saved,edges[first]

def plan(d,e):
    prior=prefix_plan(d,e);_,root,_,_=prior[5]
    sizes=parse_functions(e);size=sizes.get(root,0)
    if size!=120:raise ValueError('SC report helper prefix extent')
    ws=exact_words(d,e,root,size//4)
    n,frame,stores,loads,saved,dst=prefix(root,ws)
    if n!=13 or sizes.get(dst)!=132:raise ValueError('SC report helper first call')
    exact_words(d,e,dst,1)
    return n,frame,stores,loads,len(saved)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','SC report helper first call','SC report helper prefix extent','SC report helper stack slot','SC report helper frame',
          'SC report helper stack load','SC report helper nonvolatile'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        n,frame,stores,loads,saved=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('SC report helper prefix opcode '):
            _,_,_,_,_,kind,ordinal=reason.split()
            if kind in ('integer','load','store','branch','direct','return','system_control','other') and ordinal.isdecimal() and 1<=int(ordinal)<=32:
                print(f'POST_STM_SC_REPORT_HELPER_PREFIX verified=0 reason=opcode category={kind} ordinal={ordinal}')
                return 1
        print('POST_STM_SC_REPORT_HELPER_PREFIX verified=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_HELPER_PREFIX verified=1 labels={n} frame_bytes={frame} stack_stores={stores} stack_loads={loads} saved_nonvolatile={saved} first_call=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
