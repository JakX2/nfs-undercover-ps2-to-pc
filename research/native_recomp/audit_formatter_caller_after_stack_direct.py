#!/usr/bin/env python3
"""Aggregate-only audit of the first direct transfer after the stack copy.

Classify the exact PowerPC branch and target ownership. Do not execute it,
invent return effects, expose target addresses, or admit a new function.
"""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_stack_move_contract import plan as move_plan
from audit_formatter_caller_after_stack_move import extend
from prepare_formatter_caller_integer_contract import signed
from audit_formatter_partial_copy import boundary_shape
from make_v624_ipc_geometry import exact_words
from prepare_formatter_continuation_plan import plan as continuation_plan
from make_private_elf_symbol_map import parse_functions
from guarded_continuation import GUARD
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def audit(owner,size,contract,words,functions):
    blocks,rows,pc,w=contract
    if len(rows)!=1 or rows[0][1]>>26!=14 or rows[0][4] is not None or any(not isinstance(v,int) for _,v in rows[0][2]):
        raise ValueError('direct predecessor')
    if owner&3 or pc&3 or size!=4*len(words) or not owner<=pc<owner+size or pc!=rows[0][3] or w>>26!=18:
        raise ValueError('direct geometry')
    i=(pc-owner)//4
    body=blocks.get(owner,())
    if not 0<=i<len(body) or body[i]!=w or words[i]!=w:
        raise ValueError('direct predecessor')
    aa=bool(w&2);lk=bool(w&1)
    target=((0 if aa else pc)+signed(w&0x03fffffc,26))&0xffffffff
    if owner<=target<owner+size:
        kind='local';j=(target-owner)//4
        guarded=int(j<len(body) and body[j]==GUARD)
        admitted=int(j<len(body) and body[j]!=GUARD)
        family=boundary_shape(words[j])
    elif target in functions:
        kind='function_entry';guarded=admitted=0;family='pending'
    elif any(a<target<a+n for a,n in functions.items()):
        kind='function_interior';guarded=admitted=0;family='pending'
    else:
        kind='unresolved';guarded=admitted=0;family='pending'
    return (lk,aa,target<pc,target==pc,kind,guarded,admitted,family),target

def plan(d,e):
    move,live,cr,guards=move_plan(d,e)
    owner,size,*_=move[1]
    words=exact_words(d,e,owner,size//4)
    contract,_,_,_=extend(move,words,live,cr,continuation_plan(d,e)[6],guards)
    functions=parse_functions(e)
    result,target=audit(owner,size,contract,words,functions)
    if result[4]=='function_entry':
        result=(*result[:-1],boundary_shape(exact_words(d,e,target,1)[0]))
    return result

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','direct predecessor','direct geometry'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():lk,aa,back,self_edge,kind,guarded,admitted,family=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_AFTER_STACK_DIRECT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_AFTER_STACK_DIRECT verified=1 link={int(lk)} absolute={int(aa)} backward={int(back)} self_edge={int(self_edge)} target={kind} guarded={guarded} already_admitted={admitted} target_family={family} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
