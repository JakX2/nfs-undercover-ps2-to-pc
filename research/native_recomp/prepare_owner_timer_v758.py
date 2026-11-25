#!/usr/bin/env python3
"""Authenticate tiny original alarm timer primitives; only DEC access is eligible."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import edge
from audit_handler_deps_v749 import graph
from prepare_owner_leaf_v714 import bl
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
from prepare_v709_os_leaves import owns_root
H=0x80004000
BLR=0x4e800020
def timer_kind(words):
    if len(words)!=2 or words[1]!=BLR:raise ValueError('timer extent')
    w=words[0];op=w>>26;xo=(w>>1)&1023;spr=((w>>16)&31)|(((w>>11)&31)<<5);reg=(w>>21)&31
    if op==31 and not(w&1) and spr==22 and reg==3 and xo in (339,467):return 1 if xo==467 else 2
    return 0
def plan(dol,elf):
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n);sizes=parse_functions(elf)
    c=edge(HANDLER,handler,5)[1]
    if sizes.get(c)!=280:raise ValueError('cancel extent')
    links=graph(c,exact(dol,elf,c,70))
    if len(links)!=7 or any(k!=1 or a is None for k,a in links):raise ValueError('cancel calls')
    targets=list(dict.fromkeys(a for _,a in links[3:6]))
    roots={};kinds=[]
    for ordinal,a in enumerate(targets,1):
        if sizes.get(a)!=8:raise ValueError('timer extent')
        code=list(exact(dol,elf,a,2));kind=timer_kind(code)
        print(f'V758_TIMER_CLASS ordinal={ordinal} kind={kind}')
        if not kind:raise ValueError('timer unsupported')
        roots[a]=code;kinds.append(kind)
    roots[H]=[bl(H+4*i,a) for i,a in enumerate(targets)]+[0x60000000,BLR]
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=1+len(targets) or any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):raise ValueError('fixture overlap')
    return roots,targets,kinds
def header(p,out):
    roots,targets,kinds=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+=f'inline constexpr uint32_t H=0x{H:08x}u;\n'
    for name,values in (('targets',targets),('kinds',kinds),('caller',roots[H])):
        s+=f'inline constexpr std::array<uint32_t,{len(values)}> {name}{{'+','.join(f'0x{w:08x}u' for w in values)+'};\n'
    s+=f'inline constexpr std::array<std::array<uint32_t,2>,{len(targets)}> timer_words{{{{'+','.join('{'+','.join(f'0x{w:08x}u' for w in roots[a])+'}' for a in targets)+'}};\n'
    with out.open('x') as f:f.write(s)
def install(p,root):
    roots,targets,_=p;paths=sorted(root.glob('*.cpp'))
    if not paths or any(p.is_symlink() for p in paths):raise ValueError('private output')
    src={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=src[main].split('extern "C" void run_game(',1)[1]
    expected={a+4*i:(a,w) for a,ws in roots.items() for i,w in enumerate(ws)}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    owners=[exact_function(s,H) for s in src.values() if owns_root(s,H)]
    if len(owners)!=1:raise ValueError('caller owner')
    for i,a in enumerate(targets):verify_direct(owners[0],H+4*i,a)
    seen=set();changes={}
    for p,old in src.items():
        s=old
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(expected):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V758_NATIVE_ROUTE original_labels={2*len(targets)} direct_edges={len(targets)} fallback=0 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path);p.add_argument('--install',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        else:
            header(q,a.output);print(f'V758_TIMER_GEOMETRY verified=1 unique_roots={len(q[1])} direct_calls=3')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('timer extent','cancel extent','cancel calls','timer unsupported','fixture overlap','private output','native coverage','caller owner','hook identity','include','hook coverage')
        print('V758_TIMER_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
