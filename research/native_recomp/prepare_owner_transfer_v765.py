#!/usr/bin/env python3
"""Focused original __SITransfer with exact compiler aliases and OS leaves."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import edge
from prepare_owner_pair_v753 import plan as pair_plan,H
from audit_os_leaf_v703 import plan as leaf_plan
from prepare_owner_leaf_v714 import bl
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root
BLR=0x4e800020
def plan(dol,elf):
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    C=edge(HANDLER,handler,4)[1]
    if parse_functions(elf).get(C)!=432:raise ValueError('transfer extent')
    code=exact(dol,elf,C,108);S,R,count,sb,rb,disp,pair=pair_plan(dol,elf,4)
    d,_,r=leaf_plan(dol,elf);D,Q=d[1],r[1]
    edges=[(C+4*i,direct_bl(w,C+4*i)) for i,w in enumerate(code) if w>>26==18 and w&3==1]
    if [v for _,v in edges]!=[S,D,Q,Q,R] or count!=6:raise ValueError('transfer edges')
    roots={H:[bl(H,C),0x60000000,BLR],C:code,D:d[5],Q:r[5],S:pair[S],R:pair[R]}
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=6 or any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):raise ValueError('transfer ownership')
    return roots,C,D,Q,S,R,edges
def header(p,out):
    roots,C,D,Q,S,R,_=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+='inline constexpr uint32_t '+','.join(f'{k}=0x{a:08x}u' for k,a in zip('HCDQSR',(H,C,D,Q,S,R)))+';\n'
    for name,a in (('caller',H),('transfer_words',C),('disable_words',D),('irq_restore_words',Q),('save_words',S),('restore_words',R)):
        ws=roots[a];s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+','.join(f'0x{w:08x}u' for w in ws)+'};\n'
    with out.open('x') as f:f.write(s)
def install(p,root):
    roots,C,D,Q,S,R,edges=p
    paths=sorted(root.glob('*.cpp'));sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws)}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native labels')
    for owner,links in ((H,[(H,C)]),(C,edges)):
        owned=[exact_function(s,owner) for s in sources.values() if owns_root(s,owner)]
        if len(owned)!=1:raise ValueError('native call owner')
        for site,dst in links:verify_direct(owned[0],site,dst)
    seen=set();changes={}
    for p,old in sources.items():
        s=old
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('hook include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(expected):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V765_NATIVE_ROUTE original_labels={len(expected)-3} direct_edges=6 fallback=0 execution=0')
def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path);m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:header(p,x.output);print('V765_TRANSFER_GEOMETRY verified=1 roots=5 original_words=108 aliases=2')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('transfer extent','transfer edges','transfer ownership','native labels','native call owner','hook identity','hook include','hook coverage')
        print('V765_TRANSFER_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
