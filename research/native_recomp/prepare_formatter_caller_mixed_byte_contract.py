#!/usr/bin/env python3
"""Authenticate one post-mixed caller byte load; never execute or log private values."""
import argparse,struct
from pathlib import Path
from audit_formatter_caller_fourth_branch import plan as fourth_audit
from prepare_formatter_caller_fourth_branch_contract import extend as fourth_extend
from prepare_formatter_caller_mixed_contract import extend as mixed_extend
from audit_formatter_caller_mixed_load import audit
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from prepare_formatter_partial_native_contract import read_address
from guarded_continuation import GUARD,check_spans
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(mixed,owner,words,live,mem,initial,parent,admitted,earlier_guards):
    blocks,rows,pc,w=mixed
    if audit(mixed,live,mem,initial,parent,admitted)!=('parent',1,0,1,1,0,'const','volatile',0):
        raise ValueError('mixed byte provenance')
    size=4*len(words);body=blocks.get(owner,())
    if owner&3 or pc&3 or not 8<=size<=65536 or not owner<=pc<owner+size or len(body)>len(words):
        raise ValueError('mixed byte geometry')
    i=(pc-owner)//4
    if i>=len(body) or i+2>=len(words) or body[i]!=w or words[i]!=w or w==GUARD:
        raise ValueError('mixed byte boundary')
    if any(v!=GUARD and words[j]!=v for j,v in enumerate(body)):
        raise ValueError('mixed byte history')
    guards=set(earlier_guards)|{row[4] for row in rows if row[4] is not None}
    def inside(a):return not a&3 and owner<=a<owner+size
    if any(not inside(a) or (a-owner)//4>=len(body) or body[(a-owner)//4]!=GUARD for a in guards):
        raise ValueError('mixed byte guard')
    if pc in guards or pc+4 in guards or words[i+1]==GUARD or any(j<len(body) and body[j]!=GUARD for j in (i+1,i+2)):
        raise ValueError('mixed byte overlap')
    kind,at,n=read_address(w,live);sp=initial[1][1]
    rt=(w>>21)&31
    if kind!='stack' or n!=1 or not sp+8<=at<sp+704 or rt not in (0,*range(3,13)):
        raise ValueError('mixed byte address')
    cell=mem[at]
    if cell[0]!='byte' or not isinstance(cell[1],int) or not 0<=cell[1]<=255:
        raise ValueError('mixed byte value')
    out=list(body)+[GUARD]*max(0,i+3-len(body));out[i+1]=words[i+1]
    if any(out[(a-owner)//4]!=GUARD for a in guards):
        raise ValueError('mixed byte guard')
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(b) for a,b in expanded.items()})
    return expanded,(owner,pc,w,at-sp,cell[1],pc+4,words[i+1])

def plan(d,e):
    third,words,proof,gp,cr,saved_mask=fourth_audit(d,e,with_state=True)
    fourth,_,_=fourth_extend(third,words,proof)
    if fourth is None:raise ValueError('mixed byte predecessor')
    mixed,_,live,_=mixed_extend(fourth,words,gp,cr,saved_mask,proof[2])
    _,_,trace,admitted,entry,_=replay_plan(d,e,details=True)
    _,_,_,mem=trace[-1];_,initial,parent,_,_=entry
    return extend(mixed,fourth[1][0],words,live,mem,initial,parent,admitted,(*proof[2],fourth[1][7]))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','mixed byte provenance','mixed byte geometry','mixed byte boundary','mixed byte history','mixed byte guard','mixed byte overlap','mixed byte address','mixed byte value','mixed byte predecessor'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():_,info=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_MIXED_BYTE_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_MIXED_BYTE_CONTRACT verified=1 admitted=1 width=1 child_output_bytes=1 next_family={boundary_shape(info[-1])} next_guard=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
