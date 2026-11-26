#!/usr/bin/env python3
"""Authenticate the actual diagnostic helper's remaining branch and epilogue."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_fixture import plan as helper_plan
from prepare_post_stm_sc_report_helper import census
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from audit_osinit_suffix_v929 import category
from audit_handler_suffix_v728 import target
from prepare_stm_final_return import spr

def model(root,words,slots,frame):
    edges,reach,ret,first,_,_,_,_=census(root,words)
    if len(edges)!=2 or first not in edges:raise ValueError('helper suffix edges')
    second=max(edges)
    if not first<second or len(ret)!=1:raise ValueError('helper suffix edges')
    start=first+4;end=next(iter(ret))
    if end!=root+4*(len(words)-1):raise ValueError('helper suffix return')
    # Explore both outcomes of native conditional branches, preserving the
    # actual next-call boundary. Never assume a downstream call returned.
    work=[start];seen=set();boundaries=set();conds=[]
    while work:
        pc=work.pop()
        if pc in seen:continue
        if pc not in reach or pc<start or len(seen)>=64:raise ValueError('helper suffix escape')
        seen.add(pc);w=words[(pc-root)//4];op=w>>26
        if pc in edges or w==0x4e800020:
            boundaries.add(pc);continue
        if op==16:
            if w&3 or ((w>>21)&4)==0:raise ValueError('helper suffix branch')
            dst=target(pc,w)
            if dst<=pc:raise ValueError('helper suffix branch')
            conds.append(pc);work.extend((pc+4,dst));continue
        if op==18:
            if w&3 or target(pc,w)<=pc:raise ValueError('helper suffix branch')
            work.append(target(pc,w));continue
        if category(w) in ('system_control','other','direct'):raise ValueError('helper suffix opcode')
        work.append(pc+4)
    if second not in boundaries:raise ValueError('helper suffix second unreachable')
    # The final epilogue can be verified without actually running either callee.
    tail=words[(second+4-root)//4:];sp=-frame;loaded=set();gp={};lr=False;loads=0
    known=dict(slots)
    for i,w in enumerate(tail):
        op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31
        imm=((w&0xffff)^0x8000)-0x8000
        if w==0x4e800020:
            if i!=len(tail)-1 or sp or not lr or loaded!=set(known.values()):raise ValueError('helper suffix ABI')
        elif op in (32,46) and ra==1:
            for j in range(32-rs if op==46 else 1):
                at=sp+imm+4*j;r=rs+j;v=known.get(at)
                if v is None or v in loaded or r==1 or (v==32 and r>=14) or (v!=32 and v!=r):
                    raise ValueError('helper suffix load')
                gp[r]=v;loaded.add(v);loads+=1
        elif op==31 and xo==467 and spr(w)==8 and gp.get(rs)==32 and not lr:lr=True
        elif op==14 and rs==ra==1 and sp==-frame and imm==frame:sp=0
        else:raise ValueError('helper suffix opcode')
    return len(seen),len(conds),len(boundaries),len(tail),loads,len(loaded)-1

def plan(d,e):
    prior=helper_plan(d,e);root,_,_,_,frame=prior[3]
    words=exact_words(d,e,root,30)
    return model(root,words,prior[5],frame)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','helper suffix edges','helper suffix return','helper suffix escape','helper suffix branch','helper suffix opcode',
          'helper suffix second unreachable','helper suffix ABI','helper suffix load'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        region,conds,bounds,tail,loads,saved=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_HELPER_SUFFIX verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_HELPER_SUFFIX verified=1 region_labels={region} conditional_branches={conds} boundaries={bounds} tail_labels={tail} saved_loads={loads} nonvolatile_restores={saved} helper_return_assumed=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
