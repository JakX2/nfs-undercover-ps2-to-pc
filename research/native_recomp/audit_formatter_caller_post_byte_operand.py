#!/usr/bin/env python3
"""Aggregate-only operand provenance at the first stopped post-byte operation."""
import argparse,struct
from collections import Counter
from pathlib import Path
from prepare_formatter_caller_mixed_byte_contract import plan as byte_plan
from audit_formatter_caller_after_mixed_byte import extend as continuation
from audit_formatter_partial_integer import classify,describe
from audit_formatter_partial_copy import boundary_shape,plan as replay_plan
from guarded_continuation import GUARD
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def audit(byte,words,live,cr,saved_mask,guards,initial):
    if len(initial)!=32 or len(live)!=32:raise ValueError('post byte operand state')
    contract,reason,after,_=continuation(byte,words,live,cr,saved_mask,guards)
    blocks,rows,pc,w=contract;owner=byte[1][0]
    if len(rows)!=2 or sum(x[4] is None for x in rows)!=1 or sum(x[5] is True for x in rows)!=1 or reason!='caller integer inputs':
        raise ValueError('post byte operand predecessor')
    i=(pc-owner)//4
    if pc&3 or not 0<=i<len(words)-1 or words[i]!=w or blocks[owner][i]!=w or w==GUARD or boundary_shape(w)!='integer':
        raise ValueError('post byte operand boundary')
    name,reads,writes,*_=classify(w)
    row=describe(w,after)
    provenance=Counter()
    for r in set(reads):
        v=after[r];kind=v[0]
        if kind=='reg':
            origin=v[1]
            if not isinstance(origin,int) or not 0<=origin<32:raise ValueError('post byte operand state')
            provenance['identity']+=1
            provenance['same_entry']+=int(v==initial[r])
            provenance['entry_saved']+=int(bool(saved_mask&(1<<origin)))
        elif kind=='stack':
            provenance['same_entry']+=int(v==initial[r])
        elif kind=='partial':
            cells=v[1]
            if len(cells)!=4 or any(c[0] not in ('byte','uninitialized','part') for c in cells):
                raise ValueError('post byte operand state')
            provenance['known_partial_bytes']+=sum(c[0]=='byte' for c in cells)
            provenance['opaque_partial_bytes']+=sum(c[0]=='uninitialized' for c in cells)
        elif kind=='lr':provenance['link']+=1
    return row,provenance,sum(r in (1,2,13) for r in writes),sum(r>=14 for r in writes),sum(r>=14 and bool(saved_mask&(1<<r)) for r in writes),boundary_shape(words[i+1])

def plan(d,e):
    args=byte_plan(d,e,with_state=True)
    _,_,_,_,entry,_=replay_plan(d,e,details=True)
    return audit(*args,entry[1])

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','post byte operand state','post byte operand predecessor','post byte operand boundary','integer audit provenance'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():row,p,reserved,saved,protected,next_family=plan(q.dol.read_bytes(),q.elf.read_bytes())
        name,reads,writes,constant,stack,partial,other,cr,carry,xer,oe,alias=row
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_POST_BYTE_OPERAND verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_POST_BYTE_OPERAND verified=1 family={name} reads={reads} writes={writes} constant_inputs={constant} stack_inputs={stack} partial_inputs={partial} other_inputs={other} identity_inputs={p["identity"]} same_entry={p["same_entry"]} entry_saved={p["entry_saved"]} known_partial_bytes={p["known_partial_bytes"]} opaque_partial_bytes={p["opaque_partial_bytes"]} link_inputs={p["link"]} condition_write={cr} carry_read={carry} xer_write={xer} overflow_enable={oe} alias={alias} reserved_writes={reserved} nonvolatile_writes={saved} protected_writes={protected} next_family={next_family} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
