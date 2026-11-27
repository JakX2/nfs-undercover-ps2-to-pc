#!/usr/bin/env python3
"""Authenticate the fourth forward caller edge and preserve all previous guards.

If a selected label coincides with a prior alternate guard, report a
distinct geometry refusal. That case needs a path-sensitive guard model
rather than overwriting the earlier invariant.
"""
import argparse,struct
from pathlib import Path
from audit_formatter_caller_fourth_branch import plan as audit_plan
from audit_formatter_partial_copy import boundary_shape
from guarded_continuation import GUARD,check_spans
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(third,words,proof):
    blocks,info=third;owner,size,*_=info
    (pc,w),(kind,ctr,taken,back,dst,chosen),guards=proof
    if size!=4*len(words) or not 8<=size<=65536 or owner&3 or pc&3 or not owner<=pc<owner+size:
        raise ValueError('fourth contract geometry')
    if (pc,w)!=info[5:7] or words[(pc-owner)//4]!=w or info[7] not in guards or not 1<=len(guards)<=3 or len(set(guards))!=len(guards):
        raise ValueError('fourth contract predecessor')
    if kind!='conditional' or ctr or not isinstance(taken,bool) or back or w>>26!=16 or w&3 or not (w>>21)&4:
        raise ValueError('fourth contract edge')
    disp=w&0xfffc;disp=(disp^0x8000)-0x8000
    if dst!=pc+disp or dst<=pc+4 or chosen!=(dst if taken else pc+4):
        raise ValueError('fourth contract edge')
    other=pc+4 if taken else dst
    if any(a&3 or not owner<=a<owner+size for a in (chosen,other,*guards)):
        raise ValueError('fourth contract geometry')
    body=blocks.get(owner,());i,j,k=((a-owner)//4 for a in (pc,chosen,other))
    g=tuple((a-owner)//4 for a in guards)
    if i>=len(body) or body[i]!=w or any(a>=len(body) or body[a]!=GUARD for a in g):
        raise ValueError('fourth contract predecessor')
    if any(v!=GUARD and (a>=len(words) or v!=words[a]) for a,v in enumerate(body)):
        raise ValueError('fourth contract history')
    family=boundary_shape(words[j])
    if chosen in guards:return None,'chosen_prior_guard',family
    if j<len(body) and body[j]!=GUARD:return None,'chosen_already_admitted',family
    if k<len(body) and body[k]!=GUARD:return None,'alternate_already_admitted',family
    if words[j]==GUARD or j+1>=len(words):raise ValueError('fourth contract boundary')
    out=list(body)+[GUARD]*max(0,max(j+1,k)+1-len(body));out[j]=words[j]
    if any(out[a]!=GUARD for a in (*g,k)):raise ValueError('fourth contract guard')
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(v) for a,v in expanded.items()})
    return (expanded,(owner,size,pc,w,taken,chosen,words[j],other)),'admitted',family

def plan(d,e):
    return extend(*audit_plan(d,e,exact=True))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','fourth contract geometry','fourth contract predecessor','fourth contract edge','fourth contract history','fourth contract boundary','fourth contract guard'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():contract,reason,family=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_FOURTH_BRANCH_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_FOURTH_BRANCH_CONTRACT verified=1 admitted={int(contract is not None)} geometry={reason} next_family={family} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
