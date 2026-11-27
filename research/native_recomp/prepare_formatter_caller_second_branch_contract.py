#!/usr/bin/env python3
"""Authenticate the second caller branch without leaking original geometry.

Preserve previously admitted labels and the first branch's alternate guard.
If the second branch would reuse the first guard or an earlier native label,
report that geometry instead of silently altering the execution witness.
"""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_branch_contract import plan as first_plan
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_caller_integer_contract import plan as integer_plan
from audit_formatter_caller_branch import branch
from audit_formatter_partial_copy import boundary_shape
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(first,second,words):
    blocks,(owner,size,first_pc,first_word,first_taken,pc,w,first_other)=first
    kind,ctr,taken,back,dst,chosen=second
    if len(words)*4!=size or size>65536 or not owner<=pc<owner+size or pc&3 or words[(pc-owner)//4]!=w:
        raise ValueError('caller second branch predecessor')
    if first_taken or pc!=first_pc+4 or kind!='conditional' or ctr or taken is not True or back or dst!=chosen or dst is None or dst<=pc+4:
        raise ValueError('caller second branch edge')
    other=pc+4;body=blocks.get(owner,())
    if not owner<=first_other<owner+size or not owner<=other<owner+size or not owner<=chosen<owner+size or chosen&3:
        raise ValueError('caller second branch geometry')
    i,j,k,h=((a-owner)//4 for a in (pc,chosen,other,first_other))
    if not 0<=i<len(body) or body[i]!=w or not 0<=h<len(body) or body[h]!=GUARD:
        raise ValueError('caller second branch predecessor')
    if any(v!=GUARD and (a>=len(words) or v!=words[a]) for a,v in enumerate(body)):
        raise ValueError('caller second branch history')
    if chosen==first_other:return None,'shared_first_guard',boundary_shape(words[j])
    if j<len(body) and body[j]!=GUARD:return None,'chosen_already_admitted',boundary_shape(words[j])
    if k<len(body) and body[k]!=GUARD:return None,'alternate_already_admitted',boundary_shape(words[j])
    if words[j]==GUARD or j+1>=len(words):raise ValueError('caller second branch boundary')
    out=list(body)+[GUARD]*max(0,max(j+1,k)+1-len(body));out[j]=words[j]
    if out[h]!=GUARD or out[k]!=GUARD:raise ValueError('caller second branch guard')
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(x) for a,x in expanded.items()})
    return (expanded,(owner,size,pc,w,taken,chosen,words[j],other)), 'admitted',boundary_shape(words[j])

def plan(d,e,*,byte=None,integer=None,first=None,second=None):
    if byte is None:byte=byte_plan(d,e)
    if integer is None:integer,_=integer_plan(d,e,byte=byte)
    if first is None or second is None:first,second=first_plan(d,e,byte=byte,contract=integer)
    owner,size,*_=first[1]
    return extend(first,second,exact_words(d,e,owner,size//4))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','caller second branch predecessor','caller second branch edge','caller second branch geometry','caller second branch history','caller second branch boundary','caller second branch guard'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():contract,reason,family=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_SECOND_BRANCH_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_SECOND_BRANCH_CONTRACT verified=1 admitted={int(contract is not None)} geometry={reason} next_family={family} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
