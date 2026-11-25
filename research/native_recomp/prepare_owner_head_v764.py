#!/usr/bin/env python3
"""Compose exact original alarm head cancellation and its real timer dependencies."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_cancel_v754 import plan as cancel_plan,patch_analyzer,H
from prepare_owner_timer_v758 import plan as timer_plan
from si_nested_geometry_v693 import nested_plan
from audit_os_leaf_v703 import plan as leaf_plan
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root
def plan(dol,elf):
    roots,C,D,R,T,guards,edges=cancel_plan(dol,elf)
    timer,targets,kinds=timer_plan(dol,elf)
    if len(targets)!=1 or kinds!=[1] or set(guards)!={T,targets[0]}:raise ValueError('timer geometry')
    K=targets[0];_,root,_,_,code=nested_plan(dol,elf)
    if root!=T or len(code)!=25:raise ValueError('time geometry')
    leaves=leaf_plan(dol,elf);U=leaves[1][1]
    if (leaves[0][1],leaves[2][1])!=(D,R) or U in roots:raise ValueError('leaf geometry')
    roots[T]=code;roots[K]=timer[K];roots[U]=leaves[1][5]
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=7 or any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):raise ValueError('fixture ownership')
    return roots,C,D,R,T,U,K,edges,leaves
def header(p,out):
    roots,C,D,R,T,U,K,edges,leaves=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+='inline constexpr uint32_t '+','.join(f'{k}=0x{a:08x}u' for k,a in zip('HCDRTUK',(H,C,D,R,T,U,K)))+';\n'
    for name,a in (('caller',H),('cancel_words',C),('disable_words',D),('restore_words',R),('system_words',T),('time_words',U),('timer_words',K)):
        ws=roots[a];s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+','.join(f'0x{w:08x}u' for w in ws)+'};\n'
    s+='inline constexpr std::array<uint32_t,3> leaf_sites{'+','.join(f'0x{v[0]:08x}u' for v in leaves)+'};\n'
    s+='inline constexpr std::array<uint32_t,3> leaf_branches{'+','.join(f'0x{v[3]:08x}u' for v in leaves)+'};\n'
    with out.open('x') as f:f.write(s)
def install(p,root):
    roots,C,D,R,T,U,K,edges,leaves=p
    paths=sorted(root.glob('*.cpp'));sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws)}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native labels')
    for owner,links in ((H,[(H,C)]),(C,edges),(T,[(v[0],v[1]) for v in leaves])):
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
    print(f'V764_NATIVE_ROUTE original_labels={len(expected)-3} direct_edges=11 fallback=0 execution=0')
def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path);m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:header(p,x.output);print('V764_HEAD_GEOMETRY verified=1 roots=6 timer=1 reused_time=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('timer geometry','time geometry','leaf geometry','fixture ownership','native labels','native call owner','hook identity','hook include','hook coverage')
        print('V764_HEAD_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
