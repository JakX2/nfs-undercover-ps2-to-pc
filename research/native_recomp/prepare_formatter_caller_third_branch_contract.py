#!/usr/bin/env python3
"""Authenticate the third caller branch without altering previous guards."""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_post_integer_contract import plan as post_plan
from prepare_formatter_caller_byte_contract import plan as byte_plan
from prepare_formatter_caller_integer_contract import plan as integer_plan
from prepare_formatter_caller_branch_contract import plan as first_plan
from prepare_formatter_caller_second_branch_contract import plan as second_plan
from audit_formatter_partial_copy import boundary_shape
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(first,second,post,edge,words):
    blocks,rows,pc,w=post;owner,size,*_=second[1]
    kind,ctr,taken,back,dst,chosen=edge
    if first[1][:2]!=(owner,size) or size!=4*len(words) or not 8<=size<=65536 or owner&3 or pc&3 or not owner<=pc<owner+size:
        raise ValueError('third branch geometry')
    if not rows or rows[0][:2]!=second[1][5:7] or rows[-1][0]+4!=pc or words[(pc-owner)//4]!=w:
        raise ValueError('third branch predecessor')
    disp=w&0xfffc;disp=(disp^0x8000)-0x8000
    if kind!='conditional' or ctr or taken is not False or back or w>>26!=16 or w&3 or not (w>>21)&4 or dst!=pc+disp or chosen!=pc+4 or dst<=chosen:
        raise ValueError('third branch edge')
    if not owner<=dst<owner+size or not owner<=chosen<owner+size:
        raise ValueError('third branch geometry')
    body=blocks.get(owner,());i,j,k=((a-owner)//4 for a in (pc,chosen,dst))
    guards=tuple((a[1][7]-owner)//4 for a in (first,second))
    if not 0<=i<len(body) or body[i]!=w or any(not 0<=a<len(body) or body[a]!=GUARD for a in guards):
        raise ValueError('third branch predecessor')
    if any(v!=GUARD and (a>=len(words) or v!=words[a]) for a,v in enumerate(body)):
        raise ValueError('third branch history')
    if j in guards:return None,'chosen_prior_guard',boundary_shape(words[j])
    if j<len(body) and body[j]!=GUARD:return None,'chosen_already_admitted',boundary_shape(words[j])
    if k<len(body) and body[k]!=GUARD:return None,'alternate_already_admitted',boundary_shape(words[j])
    if words[j]==GUARD or j+1>=len(words):raise ValueError('third branch boundary')
    out=list(body)+[GUARD]*max(0,max(j+1,k)+1-len(body));out[j]=words[j]
    if any(out[a]!=GUARD for a in (*guards,k)):raise ValueError('third branch guard')
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(v) for a,v in expanded.items()})
    return (expanded,(owner,size,pc,w,False,chosen,words[j],dst)),'admitted',boundary_shape(words[j])

def plan(d,e,*,byte=None,integer=None,first=None,second=None,post=None,edge=None):
    if byte is None:byte=byte_plan(d,e)
    if integer is None:integer,_=integer_plan(d,e,byte=byte)
    if first is None or second is None:
        first,outcome=first_plan(d,e,byte=byte,contract=integer)
        second,_,_=second_plan(d,e,byte=byte,integer=integer,first=first,second=outcome)
    if second is None:raise ValueError('third branch predecessor')
    if post is None or edge is None:post,edge,_=post_plan(d,e,byte=byte,integer=integer,first=first,second=second)
    owner,size,*_=second[1]
    return extend(first,second,post,edge,exact_words(d,e,owner,size//4))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','third branch geometry','third branch predecessor','third branch edge','third branch history','third branch boundary','third branch guard'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():contract,reason,family=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_THIRD_BRANCH_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_THIRD_BRANCH_CONTRACT verified=1 admitted={int(contract is not None)} geometry={reason} next_family={family} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
