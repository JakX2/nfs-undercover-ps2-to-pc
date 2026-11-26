#!/usr/bin/env python3
"""Private control and memory census of the formatter's first direct callee."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_resume import plan as resume_plan
from prepare_post_stm_sc_report_formatter import closure
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import category
from audit_handler_suffix_v728 import target
from prepare_post_stm_sc_report_dependency_abi import classify

def census(root,ws):
    seen,bounds,back=closure(root,ws)
    rows={pc:ws[(pc-root)//4] for pc in seen}
    calls=[];returns=other=0
    for pc in bounds:
        w=rows[pc]
        if w==0x4e800020:returns+=1
        elif w>>26==18 and w&3==1:calls.append(direct_bl(w,pc))
        else:other+=1
    memory={}
    for pc,w in rows.items():
        kind=category(w)
        if kind not in ('load','store'):continue
        op=w>>26;ra=(w>>16)&31
        base='stack' if ra==1 else 'sda' if ra in (2,13) else 'argument' if 3<=ra<=10 else 'other'
        name=kind+'_'+base
        memory[name]=memory.get(name,0)+1
    return len(seen),returns,other,back,tuple(calls),memory,classify(tuple(rows.values()))

def plan(d,e):
    _,_,_,_,formatter,*_=resume_plan(d,e,details=True)
    sizes=parse_functions(e);body=exact_words(d,e,formatter,535)
    _,bounds,_=closure(formatter,body)
    targets=[direct_bl(body[(pc-formatter)//4],pc) for pc in bounds if body[(pc-formatter)//4]>>26==18 and body[(pc-formatter)//4]&3==1]
    if len(targets)!=1 or sizes.get(targets[0])!=48:raise ValueError('formatter dependency extent')
    root=targets[0];ws=exact_words(d,e,root,12)
    n,ret,other,back,calls,mem,ops=census(root,ws)
    deps=[]
    for dst in calls:
        size=sizes.get(dst,0)
        if not 4<=size<=65536 or size%4:raise ValueError('formatter dependency target')
        exact_words(d,e,dst,1);deps.append(size//4)
    return n,ret,other,back,mem,ops,deps

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','formatter dependency extent','formatter dependency target','formatter escape','formatter region cap','formatter branch','formatter boundary'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        n,ret,other,back,mem,ops,deps=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_FORMATTER_DEPENDENCY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_FORMATTER_DEPENDENCY verified=1 words=12 reachable={n} returns={ret} other_boundaries={other} backward={back} calls={len(deps)} original_execution=0')
    print('POST_STM_SC_REPORT_FORMATTER_DEPENDENCY_MEMORY '+' '.join(f'{k}={v}' for k,v in sorted(mem.items())))
    print('POST_STM_SC_REPORT_FORMATTER_DEPENDENCY_OPS '+' '.join(f'{k}={v}' for k,v in sorted(ops.items())))
    for i,n in enumerate(deps,1):print(f'POST_STM_SC_REPORT_FORMATTER_DEPENDENCY_TARGET ordinal={i} words={n}')
    return 0
if __name__=='__main__':raise SystemExit(main())
