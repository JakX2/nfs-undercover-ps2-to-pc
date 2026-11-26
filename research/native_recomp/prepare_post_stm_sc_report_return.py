#!/usr/bin/env python3
"""Authenticate the original diagnostic epilogue without assuming its callee returned."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_report_fixture import plan as prefix_plan
from prepare_post_stm_sc_report import REPORT,ROOT,EDGES
from prepare_stm_final_return import spr
from prepare_v419_full_start import MAX_DOL
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words

def epilogue(words,frame):
    if not 3<=len(words)<=12 or words[-1]!=0x4e800020:raise ValueError('SC report tail extent')
    gp={1:('stack',-frame)}
    loads=restores=0
    lr=False
    for i,w in enumerate(words):
        op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31
        imm=((w&0xffff)^0x8000)-0x8000
        if w==0x4e800020:
            if i!=len(words)-1 or not lr or gp[1]!=('stack',0) or loads!=1 or restores!=1:
                raise ValueError('SC report tail ABI')
        elif op==32 and ra==1 and rs!=1:
            if gp[1][1]+imm!=4 or loads:raise ValueError('SC report tail load')
            gp[rs]=('lr',0);loads+=1
        elif op==31 and xo==467 and spr(w)==8 and gp.get(rs)==('lr',0) and not lr:lr=True
        elif op==14 and rs==ra==1 and not restores:
            gp[1]=('stack',gp[1][1]+imm);restores+=1
        else:raise ValueError('SC report tail opcode')
    return len(words),loads,restores

def plan(d,e):
    prior=prefix_plan(d,e)
    _,_,_,_,path,fields,_=prior
    frame=fields[3]
    size=parse_functions(e).get(REPORT,0)
    if not 16<=size<=4096 or size%4:raise ValueError('SC report extent')
    ws=exact_words(d,e,REPORT,size//4)
    start=path[-1]+4
    if not REPORT<start<REPORT+size:raise ValueError('SC report tail extent')
    tail=ws[(start-REPORT)//4:]
    result=epilogue(tail,frame)
    caller=EDGES[3][0]+4
    exact_words(d,e,caller,1)
    return result,start,caller

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','SC report extent','SC report tail extent','SC report tail ABI','SC report tail load','SC report tail opcode'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        (labels,loads,restores),_,_=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_RETURN_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_RETURN_GEOMETRY verified=1 labels={labels} lr_loads={loads} frame_restores={restores} caller_verified=1 helper_return_assumed=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
