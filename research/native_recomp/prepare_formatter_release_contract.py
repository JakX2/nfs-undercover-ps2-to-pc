#!/usr/bin/env python3
"""Fail-closed private contract for exact child frame release before blr.

This does not execute the original return or assume its caller is resumed.
"""
import argparse,struct
from pathlib import Path
from audit_formatter_partial_copy import plan as replay_plan
from audit_formatter_partial_integer import special_destination
from prepare_formatter_special_contract import plan as special_plan
from prepare_formatter_nested_contract import byte_cells
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(old,row,entry,words):
    blocks,fields,rows,access,slots,known=old
    root,caller,pc,w,frame,addr,width=fields
    root2,initial,parent,caller2,_=entry
    prev,prev_word,gp,mem=row
    if (frame,addr,width,len(rows),len(access),len(known),len(slots))!=(48,0,0,96,32,5,4) or (root,caller)!=(root2,caller2):
        raise ValueError('release predecessor')
    if sum(x[4] for x in access)!=17 or len(initial)!=32 or len(gp)!=32 or initial[1][0]!='stack':
        raise ValueError('release predecessor')
    if rows[-1]!=(prev,prev_word) or prev+4!=pc or special_destination(prev_word,gp,caller)!=('link',1,1):
        raise ValueError('release link identity')
    sp=initial[1][1]
    if gp[1]!=('stack',sp-frame) or any(gp[r]!=initial[r] for r in (2,13,*range(14,32))):
        raise ValueError('release register identity')
    if tuple(mem.get(sp-frame+j) for j in range(4))!=byte_cells(initial[1],4):
        raise ValueError('release backchain')
    if any(mem.get(a)!=v for a,v in parent.items()):
        raise ValueError('release parent identity')
    for off,r in slots:
        v=('const',caller) if r==32 else initial[r]
        if tuple(mem.get(sp+off+j) for j in range(4))!=byte_cells(v,4):
            raise ValueError('release saved register')
    i=(pc-root)//4;target=pc+4
    if pc&3 or len(words)!=383 or not 0<=i<len(words)-1 or w!=(0x38210000|frame) or words[i]!=w or words[i+1]!=0x4e800020:
        raise ValueError('release instruction shape')
    live={a for a,_ in rows}
    if len(live)!=96 or pc in live or target in live or any(a&3 or not root<=a<root+4*len(words) or words[(a-root)//4]!=x for a,x in rows):
        raise ValueError('release instruction identity')
    body=blocks.get(root,())
    if i>=len(body) or body[i]!=w or (i+1<len(body) and body[i+1]!=GUARD):
        raise ValueError('release guarded words')
    out=list(body)+[GUARD]*max(0,i+3-len(body));out[i+1]=words[i+1]
    if any(x!=GUARD and out[j]!=x for j,x in enumerate(body)):
        raise ValueError('release guarded words')
    expanded={**blocks,root:tuple(out)}
    check_spans({a:4*len(x) for a,x in expanded.items()})
    return expanded,(root,caller,target,words[i+1],frame,0,0),tuple(rows)+((pc,w),),tuple(access),slots,known

def plan(d,e,*,previous=None,control=None,post=None,partial=None,special=None):
    if special is None:
        special,info=special_plan(d,e,previous=previous,control=control,post=post,partial=partial)
        if info[:2]!=('link',1):raise ValueError('release link identity')
    result,extra,trace,admitted,entry,record=replay_plan(d,e,details=True)
    if result[3:9]!=(1,1,2,2,11,'other') or result[-1]!=(4,4) or extra!=('integer',11,1,16) or len(trace)!=12:
        raise ValueError('release predecessor')
    return extend(special,trace[-1],entry,exact_words(d,e,entry[0],383))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','release predecessor','release link identity','release register identity','release backchain','release parent identity','release saved register','release instruction shape','release instruction identity','release guarded words'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():c=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_FRAME_RELEASE_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_FRAME_RELEASE_CONTRACT verified=1 labels={len(c[2])} accesses={len(c[3])} frame_release=1 nonvolatile_restored=18 caller_link=1 backchain=1 return_boundary=1 original_return=0 unknown_bytes_supplied=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
