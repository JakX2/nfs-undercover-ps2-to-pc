#!/usr/bin/env python3
"""Authenticate the first caller byte load and its next unexecuted label."""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_arrival_contract import plan as arrival_plan
from prepare_formatter_partial_native_contract import read_address
from audit_formatter_caller_load import audit
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from guarded_continuation import GUARD,check_spans
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def extend(arrival,words,gp,mem,initial,parent,admitted):
    blocks,(owner,caller,w,call)=arrival
    result=audit(w,gp,mem,initial,parent,admitted)
    if result!=('parent',1,0,1,1,0,'const','volatile',0):
        raise ValueError('caller byte provenance')
    live=list(gp);live[1]=initial[1];sp=initial[1][1]
    kind,at,n=read_address(w,live)
    if kind!='stack' or n!=1 or not sp+8<=at<sp+704 or mem[at][0]!='byte':
        raise ValueError('caller byte address')
    value=mem[at][1]
    if not 0<=value<=255:raise ValueError('caller byte value')
    i=(caller-owner)//4;body=blocks.get(owner,())
    if caller&3 or owner&3 or not 1<=i<len(body)-1 or i+2>=len(words) or body[i-1]!=call or body[i]!=w or body[i+1]!=GUARD or words[i+1]==GUARD:
        raise ValueError('caller byte boundary')
    if any(v!=GUARD and (j>=len(words) or words[j]!=v) for j,v in enumerate(body)):
        raise ValueError('caller byte history')
    if i+2<len(body) and body[i+2]!=GUARD:raise ValueError('caller byte overlap')
    out=list(body)+[GUARD]*max(0,i+3-len(body));out[i+1]=words[i+1]
    expanded={**blocks,owner:tuple(out)}
    check_spans({a:4*len(x) for a,x in expanded.items()})
    return expanded,(owner,caller,w,call,at-sp,value,caller+4,words[i+1])

def plan(d,e,*,arrival=None):
    if arrival is None:arrival=arrival_plan(d,e)
    owner=arrival[1][0];size=parse_functions(e).get(owner,0)
    if not 4<=size<=65536 or size%4:raise ValueError('caller byte extent')
    _,_,trace,admitted,entry,_=replay_plan(d,e,details=True)
    _,_,gp,mem=trace[-1];_,initial,parent,_,_=entry
    return extend(arrival,exact_words(d,e,owner,size//4),gp,mem,initial,parent,admitted)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','caller byte provenance','caller byte address','caller byte value','caller byte boundary','caller byte history','caller byte overlap','caller byte extent'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():_,info=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_BYTE_CONTRACT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_BYTE_CONTRACT verified=1 nested_visits=98 caller_loads=1 width=1 child_output_bytes=1 next_family={boundary_shape(info[-1])} next_guard=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
