#!/usr/bin/env python3
"""Authenticate a stack-relative register copy after the post-byte path.

Only a non-record OR of an identical source is admitted. No numeric guest
stack base is invented; the value stays symbolic relative to the live parent.
"""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_mixed_byte_contract import plan as byte_plan
from audit_formatter_caller_after_mixed_byte import extend as continuation
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from guarded_continuation import GUARD,check_spans
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(byte,words,live,cr,saved_mask,earlier_guards,initial):
    contract,reason,after,cr=continuation(byte,words,live,cr,saved_mask,earlier_guards)
    blocks,rows,pc,w=contract;owner=byte[1][0];size=4*len(words)
    if len(rows)!=2 or sum(x[4] is None for x in rows)!=1 or sum(x[5] is True for x in rows)!=1 or reason!='caller integer inputs':
        raise ValueError('stack move predecessor')
    if len(initial)!=32 or initial[1][0]!='stack' or after[1]!=initial[1]:
        raise ValueError('stack move frame')
    rs,ra,rb=(w>>21)&31,(w>>16)&31,(w>>11)&31
    if w>>26!=31 or (w>>1)&1023!=444 or w&1 or rs!=rb or ra==rs or ra not in (0,*range(3,13)):
        raise ValueError('stack move encoding')
    value=after[rs]
    if value[0]!='stack' or value!=initial[rs]:
        raise ValueError('stack move provenance')
    offset=value[1]-initial[1][1]
    if not isinstance(offset,int) or not 0<=offset<704:
        raise ValueError('stack move range')
    i=(pc-owner)//4;body=blocks.get(owner,())
    if pc&3 or owner&3 or not 0<=i<len(body) or i+2>=len(words) or body[i]!=w or words[i]!=w:
        raise ValueError('stack move geometry')
    guards=set(earlier_guards)|{row[4] for row in rows if row[4] is not None}
    if any(a&3 or not owner<=a<owner+4*len(body) or body[(a-owner)//4]!=GUARD for a in guards):
        raise ValueError('stack move guard')
    if pc in guards or pc+4 in guards or words[i+1]==GUARD or any(j<len(body) and body[j]!=GUARD for j in (i+1,i+2)):
        raise ValueError('stack move overlap')
    if len(body)>len(words) or any(v!=GUARD and words[j]!=v for j,v in enumerate(body)):
        raise ValueError('stack move history')
    out=list(body)+[GUARD]*max(0,i+3-len(body));out[i+1]=words[i+1]
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(b) for a,b in expanded.items()})
    result=list(after);result[ra]=value
    return (expanded,(owner,size,pc,w,offset,pc+4,words[i+1])),tuple(result),cr,tuple(sorted(guards))

def plan(d,e):
    args=byte_plan(d,e,with_state=True)
    _,_,_,_,entry,_=replay_plan(d,e,details=True)
    return extend(*args,entry[1])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','stack move predecessor','stack move frame','stack move encoding','stack move provenance','stack move range','stack move geometry','stack move guard','stack move overlap','stack move history'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():(_,info),_,_,_=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_STACK_MOVE verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_STACK_MOVE verified=1 admitted=1 family=or stack_identity=1 within_parent=1 volatile_destination=1 condition_write=0 next_family={boundary_shape(info[-1])} next_guard=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
