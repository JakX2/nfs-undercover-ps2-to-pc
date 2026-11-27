#!/usr/bin/env python3
"""Aggregate-only continuation with explicit symbolic stack pointer operands.

Do not dereference symbolic pointers or infer CR bits from numeric addresses.
The standard constant-only evaluator remains the default in all older modes.
"""
import argparse,struct
from collections import Counter
from pathlib import Path
from prepare_formatter_caller_stack_move_contract import plan as move_plan
from prepare_formatter_caller_mixed_contract import extend as mixed_extend
from prepare_formatter_caller_integer_contract import step,signed
from audit_formatter_partial_integer import classify,describe
from audit_formatter_partial_copy import boundary_shape,plan as replay_plan
from make_v624_ipc_geometry import exact_words
from prepare_formatter_continuation_plan import plan as continuation_plan
from guarded_continuation import GUARD
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

LIMIT=0x01800000
def stack_step(w,gp,*,saved_mask=0,parent):
    try:return step(w,gp,saved_mask=saved_mask)
    except ValueError as ex:
        if str(ex)!='caller integer inputs':raise
    if len(gp)!=32 or gp[1]!=('stack',parent):raise ValueError('relative stack state')
    op,rs,ra,rb,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    if op in (14,15) and ra:
        src,dst=ra,rs
        add=signed(w&0xffff,16)<<(16 if op==15 else 0)
    elif op==31 and xo==444 and not w&1 and rs==rb:
        src,dst,add=rs,ra,0
    else:raise ValueError('relative stack opcode')
    if dst not in (0,*range(3,13)):raise ValueError('relative stack destination')
    k,v=gp[src]
    if k!='stack' or not isinstance(v,int):raise ValueError('relative stack provenance')
    off=v-parent;result=off+add
    if not -LIMIT<off<LIMIT or not -LIMIT<result<LIMIT:raise ValueError('relative stack range')
    out=list(gp);out[dst]=('stack',parent+result)
    # Private proof is tagged, not a constant and never used by the old
    # fixture renderer. Native verification will resolve it against SP.
    return tuple(out),((src,('stack',off)),)

def extend(move,words,live,cr,saved_mask,guards,*,cap=16):
    blocks,(owner,size,pc,w,offset,nxt,nword)=move
    rs,ra,rb=(w>>21)&31,(w>>16)&31,(w>>11)&31
    if len(live)!=32 or live[1][0]!='stack' or w>>26!=31 or (w>>1)&1023!=444 or w&1 or rs!=rb or ra==rs or ra not in (0,*range(3,13)):
        raise ValueError('relative stack predecessor')
    parent=live[1][1]
    if live[ra]!=('stack',parent+offset) or live[rs]!=live[ra] or not -LIMIT<offset<LIMIT or nxt!=pc+4 or not guards:
        raise ValueError('relative stack predecessor')
    if size!=4*len(words) or pc&3 or owner&3 or not owner<=pc<nxt<owner+size or blocks[owner][(pc-owner)//4]!=w:
        raise ValueError('relative stack predecessor')
    anchor=(blocks,(owner,size,pc,w,False,nxt,nword,guards[0]))
    return mixed_extend(anchor,words,live,cr,saved_mask,guards,cap=cap,
                        integer_step=lambda w,gp,**kw:stack_step(w,gp,parent=parent,**kw))

def plan(d,e):
    move,live,cr,guards=move_plan(d,e)
    owner,size,*_=move[1]
    return extend(move,exact_words(d,e,owner,size//4),live,cr,continuation_plan(d,e)[6],guards)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','relative stack state','relative stack opcode','relative stack destination','relative stack provenance','relative stack range','relative stack predecessor','mixed caller geometry','mixed caller predecessor','mixed caller history','mixed caller boundary','mixed caller guard','branch provenance','branch alternate','next label conflict','next label boundary','caller integer registers','caller integer effects','caller integer opcode','caller integer encoding','caller integer inputs','cap'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():contract,reason,live,cr=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if reason not in safe:raise ValueError('relative stack predecessor')
        _,rows,_,w=contract
        family,reads,writes,constant,stack,partial,other,condition,carry,xer,oe,alias=describe(w,live)
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_AFTER_STACK_MOVE verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    counts=Counter(classify(x[1])[0] for x in rows if x[4] is None)
    relative=sum(isinstance(v,tuple) and v[0]=='stack' for x in rows for _,v in x[2])
    taken=sum(x[5] is True for x in rows);fallthrough=sum(x[5] is False for x in rows)
    print(f'FORMATTER_CALLER_AFTER_STACK_MOVE verified=1 admitted={len(rows)} integers={sum(counts.values())} branches={taken+fallthrough} taken={taken} fallthrough={fallthrough} relative_inputs={relative} next_family={boundary_shape(w)} stop_reason={reason.replace(" ","_")} established_cr_bits={sum(x is not None for x in cr)} original_execution=0')
    print(f'FORMATTER_CALLER_AFTER_STACK_MOVE_BOUNDARY family={family} reads={reads} writes={writes} constant_inputs={constant} stack_inputs={stack} partial_inputs={partial} other_inputs={other} condition_write={condition} carry_read={carry} xer_write={xer} overflow_enable={oe} alias={alias} original_execution=0')
    for name,count in sorted(counts.items()):print(f'FORMATTER_CALLER_AFTER_STACK_MOVE_FAMILY family={name} count={count}')
    return 0
if __name__=='__main__':raise SystemExit(main())
