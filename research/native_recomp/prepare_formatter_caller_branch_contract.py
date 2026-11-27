#!/usr/bin/env python3
"""Authenticate a forward local branch and keep its untaken edge guarded."""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_integer_contract import plan as integer_plan,step
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_caller_integer import after_byte
from audit_formatter_caller_branch import condition_effect,branch
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(byte,contract,gp,initial,words,saved_mask):
    blocks,rows,pc,w=contract;owner=byte[1][0];size=4*len(words)
    if len(rows)!=2 or size>65536 or owner&3 or pc&3:raise ValueError('caller branch contract predecessor')
    live,_=after_byte(byte[1],gp,initial);cr=(None,)*32
    for i,(at,word,inputs) in enumerate(rows):
        if at!=byte[1][-2]+4*i or not owner<=at<owner+size or words[(at-owner)//4]!=word:
            raise ValueError('caller branch contract predecessor')
        after,proof=step(word,live,saved_mask=saved_mask)
        if proof!=inputs:raise ValueError('caller branch contract predecessor')
        cr=condition_effect(word,live,after,cr);live=after
    if pc!=rows[-1][0]+4 or not owner<=pc<owner+size or words[(pc-owner)//4]!=w:
        raise ValueError('caller branch contract predecessor')
    kind,ctr,taken,back,dst,chosen=branch(pc,w,cr,owner,size)
    if kind not in ('conditional','direct') or ctr or taken is None or back or dst is None or chosen is None or dst<=pc+4:
        raise ValueError('caller branch contract edge')
    other=pc+4 if taken else dst
    if not owner<=other<owner+size or not owner<=chosen<owner+size or chosen==other:
        raise ValueError('caller branch contract edge')
    body=blocks.get(owner,());i=(pc-owner)//4;j=(chosen-owner)//4;k=(other-owner)//4
    if not 0<=i<len(body) or body[i]!=w:
        raise ValueError('caller branch contract source')
    # Earlier paths may already have admitted disjoint labels beyond this
    # branch. Preserve all of them; only the selected and alternate edges
    # must be previously guarded (or beyond the current fixture extent).
    if j<len(body) and body[j]!=GUARD:raise ValueError('caller branch contract chosen')
    if k<len(body) and body[k]!=GUARD:raise ValueError('caller branch contract alternate')
    if any(v!=GUARD and (a>=len(words) or v!=words[a]) for a,v in enumerate(body)):
        raise ValueError('caller branch contract history')
    if words[j]==GUARD or j+1>=len(words):
        raise ValueError('caller branch contract boundary')
    # The next label is an observation boundary, not an instruction body.
    # An already authenticated historical successor is safe to preserve;
    # all previously absent cells remain synthetic guards.
    if j+1<len(body) and body[j+1]!=GUARD and body[j+1]!=words[j+1]:
        raise ValueError('caller branch contract history')
    out=list(body)+[GUARD]*max(0,max(j+1,k)+1-len(body));out[j]=words[j]
    if out[k]!=GUARD:raise ValueError('caller branch contract alternate')
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(x) for a,x in expanded.items()})
    second=branch(chosen,words[j],cr,owner,size)
    return (expanded,(owner,size,pc,w,taken,chosen,words[j],other)),second

def plan(d,e,*,byte=None,contract=None):
    if byte is None:byte=byte_plan(d,e)
    if contract is None:contract,_=integer_plan(d,e,byte=byte)
    if contract is None:raise ValueError('caller branch contract predecessor')
    owner=byte[1][0];size=parse_functions(e).get(owner,0)
    if not 4<=size<=65536 or size%4:raise ValueError('caller branch contract predecessor')
    _,_,trace,_,entry,_=replay_plan(d,e,details=True)
    return extend(byte,contract,trace[-1][2],entry[1],exact_words(d,e,owner,size//4),continuation_plan(d,e)[6])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','caller branch contract predecessor','caller branch contract edge','caller branch contract source','caller branch contract chosen','caller branch contract alternate','caller branch contract boundary','caller branch contract history'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():(_,info),second=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_BRANCH_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    kind,ctr,taken,back,dst,chosen=second
    next_direction='unknown' if taken is None else 'taken' if taken else 'fallthrough'
    print(f'FORMATTER_CALLER_BRANCH_CONTRACT verified=1 original_branches=1 outcome={"taken" if info[4] else "fallthrough"} untaken_guard=1 next_family={boundary_shape(info[6])} second_family={kind} second_ctr_test={int(ctr)} second_outcome={next_direction} second_backward={int(back)} second_local={int(dst is not None)} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
