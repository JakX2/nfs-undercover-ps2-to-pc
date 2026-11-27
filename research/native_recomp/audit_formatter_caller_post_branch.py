#!/usr/bin/env python3
"""Audit bounded original register-only work after the two caller branches.

No initial register or condition value is invented. We reproduce the
proven byte and integer operations, follow the two authenticated branch
edges, then classify up to eight additional straight-line operations.
"""
import argparse,struct
from collections import Counter
from pathlib import Path
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_caller_integer_contract import plan as integer_plan,step
from prepare_formatter_caller_branch_contract import plan as first_plan
from prepare_formatter_caller_second_branch_contract import plan as second_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_caller_integer import after_byte
from audit_formatter_caller_branch import condition_effect,branch
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from audit_formatter_partial_integer import classify
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

CAP=8
def audit(byte,integer,first,second,gp,initial,words,saved_mask,*,cap=CAP):
    owner=byte[1][0];size=4*len(words);_,rows,end,w=integer
    if not 1<=cap<=CAP or len(rows)!=2 or size>65536 or owner&3:
        raise ValueError('post branch geometry')
    live,_=after_byte(byte[1],gp,initial);cr=(None,)*32
    def original(pc,word):
        return not pc&3 and owner<=pc<owner+size and words[(pc-owner)//4]==word
    pc=byte[1][-2]
    for at,word,inputs in rows:
        if at!=pc or not original(at,word):raise ValueError('post branch predecessor')
        after,proof=step(word,live,saved_mask=saved_mask)
        if proof!=inputs:raise ValueError('post branch predecessor')
        cr=condition_effect(word,live,after,cr);live=after;pc+=4
    if (pc,w)!=(end,integer[3]):raise ValueError('post branch predecessor')
    for n,contract in enumerate((first,second)):
        blocks,info=contract;root,extent,at,word,taken,chosen,cword,other=info
        if root!=owner or extent!=size or at!=pc or not original(at,word) or not original(chosen,cword):
            raise ValueError('post branch predecessor')
        kind,ctr,outcome,back,dst,target=branch(at,word,cr,owner,size)
        if kind!='conditional' or ctr or back or outcome is not bool(n) or taken!=outcome or target!=chosen or other!=(at+4 if outcome else dst):
            raise ValueError('post branch predecessor')
        body=blocks.get(owner,())
        j=(other-owner)//4
        if not 0<=j<len(body) or body[j]!=0x44000002:raise ValueError('post branch predecessor')
        pc=chosen
    counts=Counter();inputs=0;saved_writes=0;reason='cap'
    for _ in range(cap):
        if not owner<=pc<owner+size:raise ValueError('post branch geometry')
        word=words[(pc-owner)//4]
        try:after,proof=step(word,live,saved_mask=saved_mask)
        except ValueError as ex:
            reason=str(ex);break
        name,_,writes,*_=classify(word)
        counts[name]+=1;inputs+=len(proof);saved_writes+=sum(r>=14 for r in writes)
        cr=condition_effect(word,live,after,cr);live=after;pc+=4
    if not owner<=pc<owner+size:raise ValueError('post branch geometry')
    word=words[(pc-owner)//4]
    next_family=boundary_shape(word);next_name,reads,writes,*_=classify(word)
    kinds=Counter(live[r][0] for r in set(reads))
    return counts,inputs,saved_writes,reason,next_family,next_name,kinds,sum(x is not None for x in cr)

def plan(d,e):
    byte=byte_plan(d,e);integer,_=integer_plan(d,e,byte=byte)
    if integer is None:raise ValueError('post branch predecessor')
    first,outcome=first_plan(d,e,byte=byte,contract=integer)
    second,_,_=second_plan(d,e,byte=byte,integer=integer,first=first,second=outcome)
    if second is None:raise ValueError('post branch predecessor')
    owner,size,*_=second[1]
    _,_,trace,_,entry,_=replay_plan(d,e,details=True)
    return audit(byte,integer,first,second,trace[-1][2],entry[1],exact_words(d,e,owner,size//4),continuation_plan(d,e)[6])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','post branch geometry','post branch predecessor','caller integer registers','caller integer effects','caller integer opcode','caller integer encoding','caller integer inputs'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():counts,inputs,saved,reason,family,name,kinds,cr=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if reason not in safe|{'cap'}:raise ValueError('post branch predecessor')
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_POST_BRANCH_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_POST_BRANCH_AUDIT verified=1 admitted={sum(counts.values())} constant_inputs={inputs} saved_register_writes={saved} stop_reason={reason.replace(" ","_")} next_family={family} next_integer_family={name} next_constant_inputs={kinds["const"]} next_stack_inputs={kinds["stack"]} next_partial_inputs={kinds["partial"]} next_other_inputs={kinds["reg"]+kinds["lr"]} established_cr_bits={cr} original_execution=0')
    for name,count in sorted(counts.items()):print(f'FORMATTER_CALLER_POST_BRANCH_FAMILY family={name} count={count}')
    return 0
if __name__=='__main__':raise SystemExit(main())
