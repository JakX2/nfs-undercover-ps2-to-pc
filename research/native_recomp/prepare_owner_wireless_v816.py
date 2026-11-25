#!/usr/bin/env python3
"""Original wireless ID wrappers and bounded UnlockSram execution.

All game-derived words are private scratch output. EXI dependencies are
explicit refusal guards, never an emulated successful EXI return.
"""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE
from make_private_elf_symbol_map import parse_functions
from audit_callback_deps_v787 import CALLBACK
from audit_callback_posttime_v812 import first_roots,shared,SDK
from audit_handler_third_v740 import names,summarize
from audit_callback_frontiers_v799 import call_sites
from prepare_owner_leaf_v714 import H,bl
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_owner_scheduler_v722 import reachable
from audit_os_leaf_v703 import plan as leaf_plan
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
J=H+16
BLR=0x4e800020

def plan(dol,elf):
    sizes=parse_functions(elf)
    A,B=first_roots(CALLBACK,exact(dol,elf,CALLBACK,172))
    aw,bw=exact(dol,elf,A,39),exact(dol,elf,B,30)
    U=shared(A,aw,B,bw)
    if sizes.get(A)!=156 or sizes.get(B)!=120 or sizes.get(U)!=736:
        raise ValueError('wrapper extent')
    if [names(elf,x,SDK) for x in (A,B,U)]!=['OSSetWirelessID','OSGetWirelessID','UnlockSram']:
        raise ValueError('wrapper identity')
    uw=exact(dol,elf,U,184)
    sites=call_sites(U,uw)
    if len(sites)!=9 or any(k!=1 for _,k,_ in sites) or sites[-1][2]!=RESTORE:
        raise ValueError('unlock dependencies')
    L=sites[0][2]
    if names(elf,L,SDK)!='EXILock':raise ValueError('lock identity')
    guards=tuple(sorted({a for _,_,a in sites[:-1]}))
    if len(guards)!=7 or any(a in (H,J,A,B,U,DISABLE,RESTORE) for a in guards):
        raise ValueError('guard roots')
    for a in guards:
        if not 4<=sizes.get(a,0)<=4096:raise ValueError('guard extent')
        exact(dol,elf,a,1)
    d,_,r=leaf_plan(dol,elf)
    roots={H:[bl(H,A),0x60000000,BLR],J:[bl(J,B),0x60000000,BLR],
           A:aw,B:bw,U:uw,DISABLE:d[5],RESTORE:r[5],**{a:[BLR] for a in guards}}
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=14 or any(y>x for (_,y),(x,_) in zip(spans,spans[1:])):
        raise ValueError('root overlap')
    for a,ws in ((A,aw),(B,bw),(U,uw)):
        s,_=summarize(a,ws)
        if s['returns']!=1 or any(s[k] for k in ('indirect','tail','mtmsr','system')):
            raise ValueError('wrapper control')
    return roots,A,B,U,L,guards

def header(p,out):
    roots,A,B,U,L,guards=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n#include <span>\n'
    s+='inline constexpr uint32_t '+','.join(f'{k}=0x{v:08x}u' for k,v in (
        ('H',H),('J',J),('A',A),('B',B),('U',U),('D',DISABLE),('R',RESTORE),('L',L)))+';\n'
    fmt=lambda xs:','.join(f'0x{v:08x}u' for v in xs)
    s+=f'inline constexpr std::array<uint32_t,{len(guards)}> guards{{'+fmt(guards)+'};\n'
    for i,(a,ws) in enumerate(roots.items()):
        s+=f'inline constexpr std::array<uint32_t,{len(ws)}> words_{i}{{'+fmt(ws)+'};\n'
    s+='struct Root{uint32_t address;std::span<const uint32_t> words;};\n'
    s+=f'inline constexpr std::array<Root,{len(roots)}> roots{{{{'+','.join(
        f'Root{{0x{a:08x}u,words_{i}}}' for i,a in enumerate(roots))+'}};\n'
    with out.open('x') as f:f.write(s)

def install(p,root):
    roots,A,B,U,L,guards=p
    paths=sorted(root.glob('*.cpp'))
    if not paths or any(x.is_symlink() or x.stat().st_size>4*1024*1024 for x in paths):
        raise ValueError('private output')
    src={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=src[main].split('extern "C" void run_game(',1)[1]
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws)}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    edges=0
    for a,ws in roots.items():
        owners=[exact_function(s,a) for s in src.values() if owns_root(s,a)]
        if len(owners)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('native owner')
        for pc,k,dst in call_sites(a,ws):
            if k!=1 or dst not in roots:raise ValueError('native edge')
            verify_direct(owners[0],pc,dst);edges+=1
    seen=set();changes={}
    for p,old in src.items():
        s=old
        for pc,(a,w) in expected.items():
            if a in guards:continue
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pat.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('hook include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!={pc for pc,(a,w) in expected.items() if a not in guards}:raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V816_WIRELESS_NATIVE_ROUTE labels={len(seen)} edges={edges} exi_guards={len(guards)} fallback=0 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q,a.output)
        else:header(q,a.output);print('V816_WIRELESS_GEOMETRY verified=1 wrappers=2 unlock=1 exi_guards=7')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('wrapper extent','wrapper identity','unlock dependencies','lock identity','guard roots','guard extent','root overlap','wrapper control','private output','native coverage','native owner','native edge','hook identity','hook include','hook coverage')
        print('V816_WIRELESS_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
