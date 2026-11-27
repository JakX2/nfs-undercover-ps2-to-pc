#!/usr/bin/env python3
"""Authenticate a direct native callee entry without executing its first load.

Only aggregate geometry and provenance counts leave the private runner.
Preserve the caller's exact original BL and its guarded return address.
"""
import argparse,struct
from collections import Counter
from pathlib import Path
from audit_formatter_caller_after_stack_direct import audit as direct_audit
from audit_formatter_caller_after_stack_move import extend
from prepare_formatter_caller_stack_move_contract import plan as move_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from audit_formatter_caller_load import audit_live
from prepare_formatter_partial_native_contract import read_address
from analyze_formatter_nested_path import immutable_read
from audit_formatter_nested_read import classify_section
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from guarded_continuation import GUARD,check_spans
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def entry_contract(owner,size,contract,words,functions,entry_words,live,initial,guards):
    result,target=direct_audit(owner,size,contract,words,functions)
    lk,aa,back,self_edge,kind,_,_,_=result
    if not lk or aa or not back or self_edge or kind!='function_entry':
        raise ValueError('next call geometry')
    blocks,rows,pc,w=contract
    if len(entry_words)!=2 or not 8<=functions[target]<=65536 or functions[target]&3 or entry_words[0]==GUARD or boundary_shape(entry_words[0])!='load':
        raise ValueError('next call entry')
    if len(live)!=32 or len(initial)!=32 or initial[1][0]!='stack' or live[1]!=initial[1]:
        raise ValueError('next call state')
    if target in blocks:raise ValueError('next call root already present')
    body=blocks[owner];ret=pc+4;j=(ret-owner)//4
    if not 0<=j<len(body) or body[j]!=GUARD or ret in guards:
        raise ValueError('next call return guard')
    if any(a&3 or not owner<=a<owner+4*len(body) or body[(a-owner)//4]!=GUARD for a in guards):
        raise ValueError('next call historical guard')
    expanded={**blocks,target:(entry_words[0],GUARD)}
    check_spans({a:4*len(b) for a,b in expanded.items()})
    return expanded,(owner,size,pc,w,target,entry_words[0],ret)

def plan(d,e):
    move,live,cr,guards=move_plan(d,e)
    owner,size,*_=move[1]
    words=exact_words(d,e,owner,size//4)
    contract,_,live,cr=extend(move,words,live,cr,continuation_plan(d,e)[6],guards)
    functions=parse_functions(e)
    _,target=direct_audit(owner,size,contract,words,functions)
    _,_,trace,admitted,entry,_=replay_plan(d,e,details=True)
    _,initial,parent,_,_=entry
    _,_,_,mem=trace[-1]
    expanded,info=entry_contract(owner,size,contract,words,functions,exact_words(d,e,target,2),live,initial,guards)
    w=info[-2]
    load=audit_live(w,live,mem,initial,parent,admitted,resolve=lambda a,n:immutable_read(d,e,a,n),section=lambda a,n:classify_section(e,a,n))
    relative='none'
    try:
        site=read_address(w,live)
        if site and site[0]=='stack':
            _,at,n=site;sp=live[1][1]
            relative='above_parent' if at>=sp+704 else 'below_parent' if at+n<=sp else 'parent' if sp<=at<at+n<=sp+704 else 'cross_boundary'
    except ValueError:pass
    arguments=Counter(v[0] for v in live[3:11])
    return (expanded,info),load,relative,arguments

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','next call geometry','next call entry','next call state','next call root already present','next call return guard','next call historical guard','caller load state','caller load family'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():(_,info),load,relative,args=plan(q.dol.read_bytes(),q.elf.read_bytes())
        region,n,inherited,outputs,present,opaque,value,dest,update=load
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_NEXT_ENTRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_NEXT_ENTRY verified=1 link=1 new_root=1 guarded_return=1 entry_guard=1 stack_held=1 constant_arguments={args["const"]} stack_arguments={args["stack"]} other_arguments={8-args["const"]-args["stack"]} load_region={region} relative_region={relative} width={n} inherited_bytes={inherited} child_output_bytes={outputs} established_bytes={present} opaque_bytes={opaque} value_kind={value} destination={dest} update={update} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
