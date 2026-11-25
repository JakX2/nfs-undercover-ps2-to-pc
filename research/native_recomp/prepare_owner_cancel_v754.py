#!/usr/bin/env python3
"""Original OSCancelAlarm, with timer-reprogramming dependencies guarded."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import edge,summarize
from audit_os_leaf_v703 import plan as leaf_plan
from si_nested_geometry_v693 import nested_plan
from prepare_owner_leaf_v714 import bl
from prepare_owner_scheduler_v722 import reachable,sda_accesses,ROOT,READ,rewrite
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root
H=0x80004000
BLR=0x4e800020
def plan(dol,elf):
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n);sizes=parse_functions(elf)
    C=edge(HANDLER,handler,5)[1]
    if sizes.get(C)!=280:raise ValueError('cancel extent')
    code=list(exact(dol,elf,C,70));summary,_=summarize(C,code)
    if summary['direct']!=7 or any(summary[k] for k in ('backward','indirect','tail','mtmsr','system')) or summary['returns']!=1:raise ValueError('cancel shape')
    d,_,r=leaf_plan(dol,elf);D,R=d[1],r[1];T=nested_plan(dol,elf)[1]
    edges=[(C+4*i,direct_bl(w,C+4*i)) for i,w in enumerate(code) if w>>26==18 and w&3==1]
    if len(edges)!=7 or [v for _,v in edges[:3]]!=[D,R,T] or edges[-1][1]!=R:raise ValueError('cancel dependencies')
    # Head/tail offsets were already established by the V47 alarm init.
    # Require the original cancellation code to reference both as stores.
    if set(sda_accesses(code,36))!={-3496,-3492}:raise ValueError('cancel queue sda')
    guards=sorted({v for _,v in edges if v not in (D,R)})
    for a in guards:
        if a!=T and sizes.get(a)!=8:raise ValueError('timer guard extent')
        exact(dol,elf,a,1)
    roots={H:[bl(H,C),0x60000000,BLR],C:code,D:d[5],R:r[5]}
    for a in guards:
        if a in roots:raise ValueError('guard overlap')
        roots[a]=[BLR]
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):raise ValueError('guard overlap')
    return roots,C,D,R,T,guards,edges
def header(p,out):
    roots,C,D,R,T,guards,_=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+='inline constexpr uint32_t '+','.join(f'{k}=0x{a:08x}u' for k,a in zip('HCDRT',(H,C,D,R,T)))+';\n'
    s+=f'inline constexpr std::array<uint32_t,{len(guards)}> guard_roots{{'+','.join(f'0x{a:08x}u' for a in guards)+'};\n'
    for name,a in (('caller',H),('cancel_words',C),('disable_words',D),('restore_words',R)):
        ws=roots[a];s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+','.join(f'0x{w:08x}u' for w in ws)+'};\n'
    s+='inline constexpr std::array<uint32_t,1> guard_words{0x4e800020u};\n'
    with out.open('x') as f:f.write(s)
def patch_analyzer(p,root):
    spans=sorted((a,a+4*len(ws)) for a,ws in p[0].items())
    a=ROOT+'\n    const auto fixture_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{x:08x}u&&a<0x{y:08x}u)return 0x{x:08x}u;\n' for x,y in spans
    )+'      return 0;\n    };\n    if(fixture_owner(func_start)!=func_start)continue;'
    b='        if(fixture_owner(current_pc)!=func_start)break;\n'+READ
    f=root/'nWiiAnalyzer/src/analyzer.cpp'
    if f.is_symlink():raise ValueError('fixture ownership')
    old=f.read_text();new=rewrite(old,((ROOT,a),(READ,b)))
    if new!=old:f.write_text(new)
def install(p,root):
    roots,C,D,R,T,guards,edges=p
    paths=sorted(root.glob('*.cpp'));sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws)}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native labels')
    for owner,links in ((H,[(H,C)]),(C,edges)):
        owned=[exact_function(s,owner) for s in sources.values() if owns_root(s,owner)]
        if len(owned)!=1:raise ValueError('native call owner')
        for site,dst in links:verify_direct(owned[0],site,dst)
    hooks={pc:w for pc,(a,w) in expected.items() if a not in guards}
    seen=set();changes={}
    for p,old in sources.items():
        s=old
        for pc,w in hooks.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('hook include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(hooks):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V754_NATIVE_ROUTE original_labels={sum(a in (C,D,R) for a,w in expected.values())} guards={len(guards)} direct_edges=8 fallback=0 execution=0')
def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path);m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:
            header(p,x.output);print('V754_CANCEL_GEOMETRY verified=1 original_words=70 queue_sda=2')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('cancel extent','cancel shape','cancel dependencies','cancel queue sda','timer guard extent','guard overlap','fixture ownership','native labels','native call owner','hook identity','hook include','hook coverage')
        print('V754_CANCEL_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
