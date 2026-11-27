#!/usr/bin/env python3
"""Aggregate-only proof for bounded register/branch continuation after a caller byte."""
import argparse,struct
from collections import Counter
from pathlib import Path
from prepare_formatter_caller_mixed_byte_contract import plan as byte_plan
from prepare_formatter_caller_mixed_contract import extend as mixed_extend
from audit_formatter_partial_copy import boundary_shape
from audit_formatter_partial_integer import classify
from guarded_continuation import GUARD
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(byte,words,live,cr,saved_mask,guards,*,cap=16):
    blocks,(owner,pc,w,offset,value,next_pc,next_word)=byte
    if next_pc!=pc+4 or not 8<=offset<704 or not 0<=value<=255 or len(live)!=32 or not guards:
        raise ValueError('post byte predecessor')
    rt=(w>>21)&31
    if rt not in (0,*range(3,13)) or live[rt]!=('const',value) or not (w>>26==34 or w>>26==31 and (w>>1)&1023==87 and not w&1):
        raise ValueError('post byte state')
    body=blocks.get(owner,())
    if pc<owner or pc&3 or owner&3 or (pc-owner)//4>=len(body) or body[(pc-owner)//4]!=w or next_pc in guards or next_word==GUARD:
        raise ValueError('post byte predecessor')
    # Reuse the same bounded forward-path engine; it authenticates every
    # historical word, all previous guards and each exact new edge.
    anchor=(blocks,(owner,4*len(words),pc,w,False,next_pc,next_word,guards[0]))
    return mixed_extend(anchor,words,live,cr,saved_mask,guards,cap=cap)

def plan(d,e):
    return extend(*byte_plan(d,e,with_state=True))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','post byte predecessor','post byte state','mixed caller geometry','mixed caller predecessor','mixed caller history','mixed caller boundary','mixed caller guard','branch provenance','branch alternate','next label conflict','next label boundary','caller integer registers','caller integer effects','caller integer opcode','caller integer encoding','caller integer inputs','cap'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():contract,reason,_,cr=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if reason not in safe:raise ValueError('post byte state')
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_AFTER_MIXED_BYTE verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    _,rows,_,w=contract
    counts=Counter(classify(x[1])[0] for x in rows if x[4] is None)
    taken=sum(x[5] is True for x in rows);fallthrough=sum(x[5] is False for x in rows)
    print(f'FORMATTER_CALLER_AFTER_MIXED_BYTE verified=1 admitted={len(rows)} integers={sum(counts.values())} branches={taken+fallthrough} taken={taken} fallthrough={fallthrough} next_family={boundary_shape(w)} stop_reason={reason.replace(" ","_")} established_cr_bits={sum(x is not None for x in cr)} original_execution=0')
    for name,count in sorted(counts.items()):print(f'FORMATTER_CALLER_AFTER_MIXED_BYTE_FAMILY family={name} count={count}')
    return 0
if __name__=='__main__':raise SystemExit(main())
