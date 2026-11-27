#!/usr/bin/env python3
"""Authenticate original post-branch integer block and its next boundary."""
import argparse,struct
from pathlib import Path
from audit_formatter_caller_post_branch import audit
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_caller_integer_contract import plan as integer_plan
from prepare_formatter_caller_branch_contract import plan as first_plan
from prepare_formatter_caller_second_branch_contract import plan as second_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_caller_branch import branch
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(byte,integer,first,second,gp,initial,words,saved_mask):
    blocks,info=second;owner,size,*_=info;start,start_word=info[5:7]
    rows,end,w,_,cr,reason=audit(byte,integer,first,second,gp,initial,words,saved_mask,details=True)
    if not 1<=len(rows)<=8 or rows[0][:2]!=(start,start_word) or end!=start+4*len(rows) or w==GUARD:
        raise ValueError('post integer boundary')
    body=blocks.get(owner,());i=(start-owner)//4;j=(end-owner)//4
    if not 0<=i<len(body) or body[i]!=start_word or j+1>=len(words):
        raise ValueError('post integer boundary')
    if any(v!=GUARD and (a>=len(words) or v!=words[a]) for a,v in enumerate(body)):
        raise ValueError('post integer history')
    # Preserve all disjoint admitted labels, but do not execute over an
    # alternate guard or an already admitted historical instruction.
    guards={(first[1][7]-owner)//4,(info[7]-owner)//4}
    if any(k in guards for k in range(i,j+1)):
        raise ValueError('post integer alternate')
    if any(body[k]!=GUARD for k in range(i+1,min(j+2,len(body)))):
        raise ValueError('post integer overlap')
    out=list(body)+[GUARD]*max(0,j+2-len(body))
    for k,(_,word,_) in enumerate(rows):out[i+k]=word
    out[j]=w
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(v) for a,v in expanded.items()})
    return (expanded,rows,end,w),branch(end,w,cr,owner,size),reason

def plan(d,e,*,byte=None,integer=None,first=None,second=None):
    if byte is None:byte=byte_plan(d,e)
    if integer is None:integer,_=integer_plan(d,e,byte=byte)
    if integer is None:raise ValueError('post integer predecessor')
    if first is None or second is None:
        first,outcome=first_plan(d,e,byte=byte,contract=integer)
        second,_,_=second_plan(d,e,byte=byte,integer=integer,first=first,second=outcome)
    if second is None:raise ValueError('post integer predecessor')
    owner,size,*_=second[1]
    _,_,trace,_,entry,_=replay_plan(d,e,details=True)
    return extend(byte,integer,first,second,trace[-1][2],entry[1],exact_words(d,e,owner,size//4),continuation_plan(d,e)[6])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','post integer predecessor','post integer boundary','post integer history','post integer alternate','post integer overlap','post branch predecessor','post branch geometry'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():contract,edge,reason=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_POST_INTEGER_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    _,rows,_,w=contract;kind,ctr,taken,back,dst,chosen=edge
    direction='unknown' if taken is None else 'taken' if taken else 'fallthrough'
    print(f'FORMATTER_CALLER_POST_INTEGER_CONTRACT verified=1 admitted={len(rows)} constant_inputs={sum(len(x[2]) for x in rows)} next_family={boundary_shape(w)} next_branch={kind} next_ctr_test={int(ctr)} next_outcome={direction} next_backward={int(back)} next_local={int(dst is not None)} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
