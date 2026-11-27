#!/usr/bin/env python3
"""Aggregate-only audit of the caller's first integer operation after lbz."""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_byte_contract import plan as byte_plan
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from audit_formatter_partial_integer import classify,describe
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def after_byte(info,gp,initial):
    _,_,w,_,offset,value,_,_=info
    op,rt,xo=w>>26,(w>>21)&31,(w>>1)&1023
    if len(gp)!=32 or len(initial)!=32 or initial[1][0]!='stack' or gp[1]!=('stack',initial[1][1]-48):
        raise ValueError('caller integer state')
    if not (op==34 or op==31 and xo==87 and not w&1) or rt not in (0,*range(3,13)) or not 8<=offset<704 or not 0<=value<=255:
        raise ValueError('caller integer byte')
    live=list(gp);live[1]=initial[1];live[rt]=('const',value)
    return tuple(live),rt

def audit(info,gp,initial,following):
    live,loaded=after_byte(info,gp,initial)
    w=info[-1]
    if boundary_shape(w)!='integer':raise ValueError('caller integer family')
    name,reads,writes,*_=classify(w)
    return describe(w,live),int(loaded in reads),int(any(r in (1,2,13) for r in writes)),int(any(r>=14 for r in writes)),boundary_shape(following)

def plan(d,e):
    _,info=byte_plan(d,e)
    owner,_,_,_,_,_,pc,w=info
    size=parse_functions(e).get(owner,0)
    if not 4<=size<=65536 or size%4 or pc&3 or not owner<=pc<owner+size-4:raise ValueError('caller integer extent')
    words=exact_words(d,e,owner,size//4);i=(pc-owner)//4
    if words[i]!=w:raise ValueError('caller integer extent')
    _,_,trace,_,entry,_=replay_plan(d,e,details=True)
    return audit(info,trace[-1][2],entry[1],words[i+1])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','caller integer state','caller integer byte','caller integer family','caller integer extent','integer audit provenance'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():row,loaded,reserved,saved,next_family=plan(q.dol.read_bytes(),q.elf.read_bytes())
        name,reads,writes,constant,stack,partial,other,cr,carry,xer,oe,alias=row
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_INTEGER_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_INTEGER_AUDIT verified=1 family={name} reads={reads} writes={writes} constant_inputs={constant} stack_inputs={stack} partial_inputs={partial} other_inputs={other} condition_write={cr} carry_read={carry} xer_write={xer} overflow_enable={oe} alias={alias} reads_loaded_byte={loaded} reserved_write={reserved} nonvolatile_write={saved} next_family={next_family} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
