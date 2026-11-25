#!/usr/bin/env python3
"""Private, authenticated original context-loader fixture; no owner bytes in logs."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from prepare_v625_ipc_client import audit_native

H=0x80004000
L=0x805229b4
RFI=0x4c000064
CALLER=[0x38a50001,0x44000002,0x4e800020]

def validate_shape(code,root):
    if not 1<=len(code)<=1024 or code[-1]!=RFI or code.count(RFI)!=1:
        raise ValueError('terminal rfi')
    gqr=mtmsr=0
    for i,w in enumerate(code):
        pc=root+i*4;op=w>>26;xo=(w>>1)&1023
        if op in (16,18):
            if w&3:raise ValueError('nonlocal branch')
            bits,sign=(0xfffc,0x8000) if op==16 else (0x3fffffc,0x2000000)
            dst=pc+((w&bits)^sign)-sign
            if not root<=dst<root+4*len(code):raise ValueError('nonlocal branch')
        if op==17 or (op==19 and xo in (16,528)):raise ValueError('unexpected control')
        if op==31 and xo==146:mtmsr+=1
        if op==31 and xo==467:
            spr=((w>>11)&31)*32+((w>>16)&31)
            if 912<=spr<=919:
                bit=1<<(spr-912)
                if gqr&bit:raise ValueError('duplicate gqr restore')
                gqr|=bit
    if mtmsr!=1:raise ValueError('mtmsr shape')
    return gqr

def plan(dol,elf):
    n=parse_functions(elf).get(L)
    if n!=54*4:raise ValueError('extent')
    code=list(exact(dol,elf,L,n//4))
    return code,validate_shape(code,L)

def header(code,gqr,out):
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    s+=f'inline constexpr uint32_t H=0x{H:08x}u,L=0x{L:08x}u,GqrMask={gqr}u;\n'
    for name,words in (('resume_words',CALLER),('loader_words',code)):
        s+=f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(f'0x{w:08x}u' for w in words)+'};\n'
    with out.open('x') as f:f.write(s)

def install(code,root):
    paths=sorted(root.glob('*.cpp'))
    if not paths or any(p.is_symlink() for p in paths):raise ValueError('private output')
    sources={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=sources[main].split('extern "C" void run_game(',1)[1]
    all_labels={a+4*i:(a,w) for a,ws in ((H,CALLER),(L,code)) for i,w in enumerate(ws)}
    if audit_native(sources.values(),outer,all_labels)!=len(all_labels):raise ValueError('native coverage')
    hooks={L+4*i:w for i,w in enumerate(code)}
    hooks[H]=CALLER[0]
    seen=set();changes={}
    for p,old in sources.items():
        s=old
        for pc,w in hooks.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            matches=list(pat.finditer(s))
            if not matches:continue
            if len(matches)!=1 or pc in seen:raise ValueError('label identity')
            seen.add(pc)
            s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(hooks):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V720_NATIVE_ROUTE loader_labels={len(code)} resume_labels=3 hooked={len(hooks)} fallback=0 execution=0')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path);p.add_argument('--install',action='store_true')
    a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        code,gqr=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(code,a.output)
        else:
            header(code,gqr,a.output)
            print(f'V720_OWNER_CONTEXT_GEOMETRY verified=1 words={len(code)} gqr_restores={gqr.bit_count()} mtmsr=1 rfi=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError):
        print('V720_CONTEXT_PREP verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
