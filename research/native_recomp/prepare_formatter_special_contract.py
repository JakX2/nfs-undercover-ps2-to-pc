#!/usr/bin/env python3
"""Private single-step continuation of the 95-instruction formatter witness.

Only a known-source LR/CTR write is admitted. No memory, GPR, CR or XER
effects are invented; the next original word remains an unexecuted boundary.
"""
import argparse,struct
from pathlib import Path
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from audit_formatter_partial_integer import special_destination
from prepare_formatter_partial_native_contract import plan as partial_plan
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(old,row,words):
    blocks,fields,rows,access,slots,known=old
    root,caller,pc,w,frame,addr,width=fields
    if (frame,addr,width,len(rows),len(access),len(known),len(slots))!=(48,0,0,95,32,5,4):
        raise ValueError('special continuation predecessor')
    if sum(x[4] for x in access)!=17 or len(set(a for a,_ in rows))!=95:
        raise ValueError('special continuation predecessor')
    at,word,gp,mem=row
    if (at,word)!=(pc,w) or len(gp)!=32 or root not in blocks:
        raise ValueError('special continuation identity')
    kind,known_source,caller_match=special_destination(w,gp,caller)
    if kind not in ('link','count') or not known_source:
        raise ValueError('special continuation source')
    # No control edge is taken by mtlr/mtctr. The next instruction is
    # authenticated from the same function and never executed by this plan.
    i=(pc-root)//4;target=pc+4
    if pc&3 or len(words)!=383 or not 0<=i<len(words)-1 or words[i]!=w or words[i+1]==GUARD:
        raise ValueError('special continuation words')
    visited={a for a,_ in rows}
    if pc in visited or target in visited or any(a&3 or not root<=a<root+4*len(words) or words[(a-root)//4]!=x for a,x in rows):
        raise ValueError('special continuation overlap')
    body=blocks[root]
    if i>=len(body) or body[i]!=w or (i+1<len(body) and body[i+1]!=GUARD):
        raise ValueError('special continuation old words')
    out=list(body)+[GUARD]*max(0,i+3-len(body))
    out[i+1]=words[i+1]
    if any(x!=GUARD and out[j]!=x for j,x in enumerate(body)):
        raise ValueError('special continuation old words')
    expanded={**blocks,root:tuple(out)}
    check_spans({a:4*len(x) for a,x in expanded.items()})
    return (expanded,(root,caller,target,words[i+1],frame,0,0),tuple(rows)+((pc,w),),tuple(access),slots,known),(kind,caller_match,boundary_shape(words[i+1]))

def plan(d,e,*,previous=None,control=None,post=None,partial=None):
    result,extra,trace,admitted,entry,record=replay_plan(d,e,details=True)
    if result[3:9]!=(1,1,2,2,11,'other') or result[-1]!=(4,4) or extra!=('integer',11,1,16) or len(trace)!=12:
        raise ValueError('special continuation replay')
    if partial is None:partial=partial_plan(d,e,previous=previous,control=control,post=post)
    return extend(partial,trace[-1],exact_words(d,e,entry[0],383))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','special continuation predecessor','special continuation identity','special continuation source','special continuation words','special continuation overlap','special continuation old words','special continuation replay'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            contract,(kind,match,next_family)=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_SPECIAL_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_SPECIAL_CONTRACT verified=1 labels={len(contract[2])} accesses={len(contract[3])} loads=15 stores=17 special={kind} caller_link_match={match} next_family={next_family} unknown_bytes_supplied=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
