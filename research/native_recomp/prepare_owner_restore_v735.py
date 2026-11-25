#!/usr/bin/env python3
"""Owner-only exact compiler GPR restore suffix fixture."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER,shape
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from classify_save_leaf_v683 import symbol_evidence
from si_helper_geometry_v680 import alias_owner
from audit_handler_suffix_v728 import restore_suffix
from prepare_owner_leaf_v714 import bl
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
from prepare_v709_os_leaves import owns_root
H=0x80004000
BLR=0x4e800020
def plan(dol,elf):
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    _,direct,indirect=shape(HANDLER,handler)
    sites=sorted([p for p,_ in direct]+list(indirect))
    if len(sites)<12:raise ValueError('call census')
    site=sites[11];targets=dict(direct)
    if site not in targets:raise ValueError('restore edge')
    root=targets[site];sizes=parse_functions(elf)
    if root in sizes:raise ValueError('restore alias')
    code=list(exact(dol,elf,root,16))
    if restore_suffix(code)!=15:raise ValueError('restore shape')
    alias_owner(root,len(code)*4,sizes)
    ev=symbol_evidence(elf,root)
    if not(ev['zero_func'] or ev['notype']):raise ValueError('restore symbol')
    first=code[0];base=(first>>16)&31;disp=((first&0xffff)^0x8000)-0x8000
    return root,code,base,disp
def caller(root):return [bl(H,root),0x60000000,BLR]
def header(p,out):
    root,code,base,disp=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+=f'inline constexpr uint32_t H=0x{H:08x}u,L=0x{root:08x}u,Base={base}u;\ninline constexpr int32_t Disp={disp};\n'
    for name,words in (('resume_words',caller(root)),('loader_words',code)):
        s+=f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(f'0x{w:08x}u' for w in words)+'};\n'
    with out.open('x') as f:f.write(s)
def install(p,root):
    L,code,_,_=p;paths=sorted(root.glob('*.cpp'))
    if not paths or any(p.is_symlink() for p in paths):raise ValueError('private output')
    src={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=src[main].split('extern "C" void run_game(',1)[1]
    expected={a+4*i:(a,w) for a,ws in ((H,caller(L)),(L,code)) for i,w in enumerate(ws)}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    owners=[exact_function(s,H) for s in src.values() if owns_root(s,H)]
    if len(owners)!=1:raise ValueError('caller owner')
    verify_direct(owners[0],H,L)
    hooks={pc:w for pc,(_,w) in expected.items()};seen=set();changes={}
    for p,s in src.items():
        old=s
        for pc,w in hooks.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(hooks):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print('V735_NATIVE_ROUTE labels=19 original_labels=16 direct_edges=1 fallback=0 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path);p.add_argument('--install',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        plan_=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(plan_,a.output)
        else:
            header(plan_,a.output)
            print('V735_RESTORE_GEOMETRY verified=1 original_words=16 gpr_loads=15 alias=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('call census','restore edge','restore alias','restore shape','restore symbol','private output','native coverage','caller owner','hook identity','include','hook coverage')
        print('V735_RESTORE_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
