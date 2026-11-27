#!/usr/bin/env python3
"""Aggregate-only audit of the fourth caller branch after a proven comparison."""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_caller_integer_contract import plan as integer_plan
from prepare_formatter_caller_branch_contract import plan as first_plan
from prepare_formatter_caller_second_branch_contract import plan as second_plan
from prepare_formatter_caller_post_integer_contract import plan as post_plan
from prepare_formatter_caller_third_branch_contract import plan as third_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_caller_post_branch import audit as post_audit
from audit_formatter_caller_branch import branch
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from guarded_continuation import GUARD
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def audit(first,second,post,third,words,details,*,exact=False):
    blocks,info=third;owner,size,pc,w,taken,at,next_word,other=info
    rows,end,word,_,cr,_=details
    if first[1][:2]!=(owner,size) or second[1][:2]!=(owner,size) or len(words)*4!=size or size>65536 or owner&3:
        raise ValueError('fourth branch geometry')
    if (rows,end,word)!=post[1:] or (pc,w)!=(end,word) or taken or at!=pc+4:
        raise ValueError('fourth branch predecessor')
    kind,ctr,outcome,back,dst,chosen=branch(pc,w,cr,owner,size)
    if kind!='conditional' or ctr or outcome is not False or back or dst!=other or chosen!=at:
        raise ValueError('fourth branch predecessor')
    if not owner<=at<owner+size or words[(at-owner)//4]!=next_word:
        raise ValueError('fourth branch predecessor')
    body=blocks.get(owner,())
    guards={first[1][7],second[1][7],other}
    if any(not owner<=a<owner+size or a&3 or (a-owner)//4>=len(body) or body[(a-owner)//4]!=GUARD for a in guards):
        raise ValueError('fourth branch predecessor')
    if any(v!=GUARD and (i>=len(words) or v!=words[i]) for i,v in enumerate(body)):
        raise ValueError('fourth branch history')
    if (at-owner)//4>=len(body) or body[(at-owner)//4]!=next_word:
        raise ValueError('fourth branch predecessor')
    kind,ctr,outcome,back,dst,chosen=branch(at,next_word,cr,owner,size)
    alternate=None if chosen is None else at+4 if outcome else dst
    def occupied(a):
        return a is not None and 0<=(a-owner)//4<len(body) and body[(a-owner)//4]!=GUARD
    if exact:return (at,next_word),(kind,ctr,outcome,back,dst,chosen),tuple(sorted(guards))
    return kind,ctr,outcome,back,int(dst is not None),int(chosen in guards),int(occupied(chosen)),int(occupied(alternate)),boundary_shape(words[(chosen-owner)//4]) if chosen is not None else 'unresolved',sum(x is not None for x in cr)

def plan(d,e,*,exact=False):
    byte=byte_plan(d,e);integer,_=integer_plan(d,e,byte=byte)
    if integer is None:raise ValueError('fourth branch predecessor')
    first,outcome=first_plan(d,e,byte=byte,contract=integer)
    second,_,_=second_plan(d,e,byte=byte,integer=integer,first=first,second=outcome)
    if second is None:raise ValueError('fourth branch predecessor')
    post,edge,_=post_plan(d,e,byte=byte,integer=integer,first=first,second=second)
    third,_,_=third_plan(d,e,byte=byte,integer=integer,first=first,second=second,post=post,edge=edge)
    if third is None:raise ValueError('fourth branch predecessor')
    owner,size,*_=third[1];words=exact_words(d,e,owner,size//4)
    _,_,trace,_,entry,_=replay_plan(d,e,details=True)
    details=post_audit(byte,integer,first,second,trace[-1][2],entry[1],words,continuation_plan(d,e)[6],details=True)
    result=audit(first,second,post,third,words,details,exact=exact)
    return (third,words,result) if exact else result

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','fourth branch geometry','fourth branch predecessor','fourth branch history'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():kind,ctr,taken,back,local,prior,chosen,alternate,family,known=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_FOURTH_BRANCH_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    direction='unknown' if taken is None else 'taken' if taken else 'fallthrough'
    print(f'FORMATTER_CALLER_FOURTH_BRANCH_AUDIT verified=1 family={kind} ctr_test={int(ctr)} outcome={direction} backward_edge={int(back)} local_target={local} chosen_prior_guard={prior} chosen_already_admitted={chosen} alternate_already_admitted={alternate} next_family={family} established_cr_bits={known} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
