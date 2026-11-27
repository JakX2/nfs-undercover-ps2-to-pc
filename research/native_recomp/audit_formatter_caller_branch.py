#!/usr/bin/env python3
"""Determine the first caller branch from only newly proven CR bits.

The nested formatter's inherited CR and CTR are not assumed. Record-form
integer instructions establish LT/GT/EQ, but never invent XER.SO.
"""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_integer_contract import plan as integer_plan,step,signed
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_caller_integer import after_byte
from audit_formatter_partial_integer import classify
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def condition_effect(w,gp,after,cr):
    if len(cr)!=32:raise ValueError('caller branch CR geometry')
    _,_,writes,cr_write,_,_,_=classify(w)
    if not cr_write:return tuple(cr)
    op,ra,rb,xo=w>>26,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    if op in (10,11) or op==31 and xo in (0,32):
        field=(w>>23)&7
        a=gp[ra][1]
        b=(w&0xffff) if op==10 else signed(w&0xffff,16) if op==11 else gp[rb][1]
        if op==11 or op==31 and xo==0:a=signed(a)
        if op==31 and xo==0:b=signed(b)
    else:
        if len(writes)!=1 or after[writes[0]][0]!='const':raise ValueError('caller branch CR effect')
        field=0;a=signed(after[writes[0]][1]);b=0
    out=list(cr);out[field*4:field*4+4]=[a<b,a>b,a==b,None]
    return tuple(out)

def branch(pc,w,cr,owner,size):
    if len(cr)!=32 or owner&3 or pc&3 or not 4<=size<=65536 or size%4 or not owner<=pc<owner+size:
        raise ValueError('caller branch geometry')
    op=w>>26
    if op not in (16,18) or w&3:return ('unsupported',False,None,False,None,None)
    if op==18:
        dst=pc+signed(w&0x03fffffc,26)
        kind='direct';ctr=False;taken=True
    else:
        bo=(w>>21)&31;bi=(w>>16)&31
        dst=pc+signed(w&0xfffc,16)
        kind='conditional';ctr=not bool(bo&4)
        match=True if bo&16 else None if cr[bi] is None else cr[bi]==bool(bo&8)
        # A known false CR predicate decides a branch even with unknown CTR,
        # but its counter update is still not authorized for native execution.
        taken=False if match is False else None if ctr else match
    inside=owner<=dst<owner+size and not dst&3
    if not inside:return (kind,ctr,taken,dst<=pc,None,None)
    chosen=None if taken is None else dst if taken else pc+4
    if chosen is not None and not owner<=chosen<owner+size:chosen=None
    return kind,ctr,taken,dst<=pc,dst,chosen

def audit(byte,contract,gp,initial,words,saved_mask):
    blocks,rows,pc,w=contract;owner=byte[1][0]
    if not rows or len(rows)>8 or len(words)*4>65536:raise ValueError('caller branch predecessor')
    live,_=after_byte(byte[1],gp,initial);cr=(None,)*32
    for i,(at,word,inputs) in enumerate(rows):
        if at!=byte[1][-2]+4*i or not owner<=at<owner+4*len(words) or words[(at-owner)//4]!=word:
            raise ValueError('caller branch predecessor')
        after,proof=step(word,live,saved_mask=saved_mask)
        if proof!=inputs:raise ValueError('caller branch predecessor')
        cr=condition_effect(word,live,after,cr);live=after
    if pc!=rows[-1][0]+4 or not owner<=pc<owner+4*len(words) or words[(pc-owner)//4]!=w:
        raise ValueError('caller branch predecessor')
    kind,ctr,taken,back,dst,chosen=branch(pc,w,cr,owner,len(words)*4)
    body=blocks.get(owner,())
    def occupied(at):
        return at is not None and 0<=(at-owner)//4<len(body) and body[(at-owner)//4]!=0x44000002
    next_family=boundary_shape(words[(chosen-owner)//4]) if chosen is not None else 'unresolved'
    return kind,ctr,taken,back,int(dst is not None),int(occupied(dst)),int(occupied(chosen)),next_family,sum(x is not None for x in cr)

def plan(d,e):
    byte=byte_plan(d,e);contract,_=integer_plan(d,e,byte=byte)
    if contract is None or len(contract[1])!=2:raise ValueError('caller branch predecessor')
    owner=byte[1][0];size=parse_functions(e).get(owner,0)
    if not 4<=size<=65536 or size%4:raise ValueError('caller branch geometry')
    _,_,trace,_,entry,_=replay_plan(d,e,details=True)
    return audit(byte,contract,trace[-1][2],entry[1],exact_words(d,e,owner,size//4),continuation_plan(d,e)[6])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','caller branch predecessor','caller branch geometry','caller branch CR geometry','caller branch CR effect'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():kind,ctr,taken,back,local,occupied,chosen,next_family,known=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_BRANCH_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    direction='unknown' if taken is None else 'taken' if taken else 'fallthrough'
    print(f'FORMATTER_CALLER_BRANCH_AUDIT verified=1 family={kind} ctr_test={int(ctr)} outcome={direction} backward_edge={int(back)} local_target={local} target_already_admitted={occupied} chosen_already_admitted={chosen} next_family={next_family} established_cr_bits={known} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
