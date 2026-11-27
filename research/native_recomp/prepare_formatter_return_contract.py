#!/usr/bin/env python3
"""Authenticate the original nested return and its deliberately guarded caller.

The caller's actual next word is inspected privately, not installed or
executed by the return-only checkpoint.
"""
import argparse,struct
from pathlib import Path
from prepare_formatter_release_contract import plan as release_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from guarded_continuation import GUARD
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL,direct_bl
from private_plan_cache import plan_cache_scope

def contract(release,prior,words,gp):
    blocks,fields,rows,access,slots,known=release
    child,caller,ret,word,frame,addr,width=fields
    parent_blocks,parent,start,dst,entry,active,mask,args=prior
    if (len(rows),len(access),frame,addr,width,word)!=(97,32,48,0,0,0x4e800020):
        raise ValueError('return predecessor')
    if child!=dst or parent==child or not active or len(gp)!=32 or mask.bit_count()!=16:
        raise ValueError('return caller identity')
    call,call_word=active[-1]
    if caller!=call+4 or call_word>>26!=18 or call_word&3!=1 or direct_bl(call_word,call)!=child:
        raise ValueError('return call identity')
    if not parent<=call<caller or caller&3 or (caller-parent)//4>=len(words):
        raise ValueError('return caller extent')
    i=(caller-parent)//4
    body=blocks.get(parent,())
    if not 1<=i<len(body) or body[i-1]!=call_word or body[i]!=GUARD or words[i-1]!=call_word:
        raise ValueError('return caller guard')
    if blocks.get(parent)!=parent_blocks.get(parent) or not words[i] or words[i]==GUARD:
        raise ValueError('return caller guard')
    cbody=blocks.get(child,());j=(ret-child)//4
    if ret&3 or not 1<=j<len(cbody) or cbody[j]!=word or rows[-1]!=(ret-4,0x38210000|frame):
        raise ValueError('return epilogue identity')
    # No value of the return register or first caller instruction leaks.
    return parent,caller,GUARD,boundary_shape(words[i]),gp[3][0]

def plan(d,e,*,release=None,previous=None):
    if previous is None:previous=continuation_plan(d,e)
    if release is None:release=release_plan(d,e)
    _,_,trace,_,_,_=replay_plan(d,e,details=True)
    size=parse_functions(e).get(previous[1],0)
    if not 4<=size<=65536 or size%4:raise ValueError('return caller extent')
    return contract(release,previous,exact_words(d,e,previous[1],size//4),trace[-1][2])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','return predecessor','return caller identity','return call identity','return caller extent','return caller guard','return epilogue identity'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():_,_,_,family,kind=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if kind not in ('const','stack','partial','reg','lr'):raise ValueError('return caller identity')
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_RETURN_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_RETURN_CONTRACT verified=1 labels=98 prior_accesses=32 exact_blr=1 original_call=1 caller_guard=1 caller_word_authenticated=1 caller_family={family} return_value_kind={kind} caller_body_executed=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
