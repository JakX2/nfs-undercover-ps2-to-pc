#!/usr/bin/env python3
"""Authenticate the original paired GPR save/restore aliases in SI transfer roots."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from classify_save_leaf_v683 import classify_suffix,symbol_evidence
from si_helper_geometry_v680 import alias_owner
from audit_handler_suffix_v728 import restore_suffix
from audit_handler_third_v740 import edge
from audit_handler_deps_v749 import graph
from prepare_owner_leaf_v714 import bl
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
from prepare_v709_os_leaves import owns_root
H=0x80004000
BLR=0x4e800020
def alias(dol,elf,root,sizes,count):
    if root in sizes:raise ValueError('alias root')
    alias_owner(root,4*(count+1),sizes)
    ev=symbol_evidence(elf,root)
    if not(ev['zero_func'] or ev['notype']):raise ValueError('alias symbol')
    return list(exact(dol,elf,root,count+1))
def pair_shape(save,restore,count):
    info=classify_suffix(save)
    if info['kind']!=1 or info['registers']!=count or restore_suffix(restore)!=count:raise ValueError('pair shape')
    a,b=save[0],restore[0]
    disp=lambda w:((w&0xffff)^0x8000)-0x8000
    if disp(a)!=disp(b):raise ValueError('frame offset')
    return info['base'],(b>>16)&31,disp(a)
def caller(S,R,count):
    words=[bl(H,S)]+[(14<<26)|(reg<<21)|0x1234 for reg in range(32-count,32)]
    words.extend((bl(H+4*len(words),R),0x60000000,BLR))
    return words
def plan(dol,elf,lane):
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n);sizes=parse_functions(elf)
    root=edge(HANDLER,handler,lane)[1]
    extent,count,calls={4:(108,6,5),7:(91,11,9)}[lane]
    if sizes.get(root)!=4*extent:raise ValueError('parent extent')
    code=exact(dol,elf,root,extent)
    edges=graph(root,code)
    if len(edges)!=calls or any(kind!=1 or dst is None for kind,dst in edges):raise ValueError('parent calls')
    S,R=edges[0][1],edges[-1][1]
    save=alias(dol,elf,S,sizes,count);restore=alias(dol,elf,R,sizes,count)
    sb,rb,disp=pair_shape(save,restore,count)
    roots={H:caller(S,R,count),S:save,R:restore}
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=3 or any(b>c for (_,b),(c,_) in zip(spans,spans[1:])):raise ValueError('fixture overlap')
    return S,R,count,sb,rb,disp,roots
def header(p,out):
    S,R,n,sb,rb,disp,roots=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+=f'inline constexpr uint32_t H=0x{H:08x}u,S=0x{S:08x}u,R=0x{R:08x}u;\ninline constexpr unsigned Count={n},SaveBase={sb},RestoreBase={rb};\ninline constexpr int32_t Disp={disp};\n'
    for name,a in (('caller_words',H),('save_words',S),('restore_words',R)):
        ws=roots[a];s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+','.join(f'0x{w:08x}u' for w in ws)+'};\n'
    with out.open('x') as f:f.write(s)
def install(p,root):
    S,R,n,_,_,_,roots=p;paths=sorted(root.glob('*.cpp'))
    if not paths or any(p.is_symlink() for p in paths):raise ValueError('private output')
    src={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=src[main].split('extern "C" void run_game(',1)[1]
    expected={a+4*i:(a,w) for a,ws in roots.items() for i,w in enumerate(ws)}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    owners=[exact_function(s,H) for s in src.values() if owns_root(s,H)]
    if len(owners)!=1:raise ValueError('caller owner')
    verify_direct(owners[0],H,S);verify_direct(owners[0],H+4*(n+1),R)
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
    print(f'V753_NATIVE_ROUTE original_labels={2*(n+1)} direct_edges=2 fallback=0 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path);p.add_argument('lane',type=int,choices=(4,7));p.add_argument('--install',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes(),a.lane)
        if a.install:install(q,a.output)
        else:
            header(q,a.output)
            print(f'V753_PAIR_GEOMETRY lane={a.lane} verified=1 gprs={q[2]} matched_frame=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('alias root','alias symbol','pair shape','frame offset','parent extent','parent calls','fixture overlap','private output','native coverage','caller owner','hook identity','include','hook coverage')
        print(f'V753_PAIR_PREP lane={a.lane} verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
