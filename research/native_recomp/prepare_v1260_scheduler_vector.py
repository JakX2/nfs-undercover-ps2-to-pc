#!/usr/bin/env python3
"""Owner-private scheduler to external vector/trampoline fixture."""
import argparse,re,struct
from pathlib import Path
from make_v626_ipc_fixture import assemble
from make_v624_ipc_geometry import ROOT,exact_words
from make_v651_open_fixture import SOURCE as SC_SOURCE
from audit_v662_external_overlay import expected,VECTOR,SOURCE
from prepare_v453_debug_leaf import data_at,VECTORS
from prepare_v663_external_entry import TRAMP,DISPATCH
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import words_at,MAX_DOL
from prepare_v1259_scheduler_vector import prepare as verify_vector
from prepare_v625_ipc_client import audit_native
from apply_bat_roots_v586 import ROOT as ANALYZE_ROOT,READ
from apply_irq_bootstrap_v475 import rewrite
from audit_handler_suffix_v728 import target
BLR=0x4e800020

def geometry(dol,elf):
    verify_vector(dol,elf)
    if parse_functions(elf).get(TRAMP)!=80:raise ValueError('trampoline extent')
    t=exact_words(dol,elf,TRAMP,20)
    if t[-1]>>26!=18 or t[-1]&3 or target(TRAMP+76,t[-1])!=DISPATCH:raise ValueError('trampoline tail')
    return tuple(expected(dol)),t,exact_words(dol,elf,DISPATCH,1)[0]

def extend(raw,csv,source,table,t,dispatcher):
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if name!=f'func_{pc:08X}' or not size or size%4 or pc in blocks:raise ValueError('symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    if set(blocks)&{VECTOR,TRAMP,DISPATCH,SOURCE,SC_SOURCE} or len(source)!=38 or len(table)!=60 or len(t)!=20:
        raise ValueError('fixture geometry')
    blocks[TRAMP]=t;blocks[DISPATCH]=(dispatcher,BLR)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{4*len(ws)}\n' for pc,ws in sorted(blocks.items()))
    image=bytearray(assemble({**blocks,SOURCE:source,SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    # Supply the original vector offset table to the existing external overlay.
    for off,v in ((0x1c,len(image)),(0x64,VECTORS),(0xac,len(table))):
        if struct.unpack_from('>I',image,off)[0]:raise ValueError('data slot')
        struct.pack_into('>I',image,off,v)
    return bytes(image)+table,csv

def render(v,t,d):
    f=lambda ws:','.join(f'0x{w:08x}u' for w in ws)
    return ('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v1260 {\n'
        f'inline constexpr uint32_t trampoline=0x{TRAMP:08x}u,dispatcher=0x{DISPATCH:08x}u,dispatcher_word=0x{d:08x}u;\n'
        f'inline constexpr std::array<uint32_t,38> vector_words{{{f(v)}}};\n'
        f'inline constexpr std::array<uint32_t,20> trampoline_words{{{f(t)}}};\n}}\n')

def analyzer(s,dispatcher_size=8):
    if dispatcher_size not in (8,0x2a4):raise ValueError('dispatcher extent')
    spans=((VECTOR,152),(TRAMP,80),(DISPATCH,dispatcher_size))
    roots=ANALYZE_ROOT+'\n    const auto ipc_vector_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in spans)+
        '      return 0;\n    };\n    if(ipc_vector_owner(func_start)&&ipc_vector_owner(func_start)!=func_start)continue;'
    read='        const auto ipc_vector_root=ipc_vector_owner(current_pc);\n        if((ipc_vector_root&&ipc_vector_root!=func_start)||(ipc_vector_owner(func_start)&&ipc_vector_root!=func_start))break;\n'+READ
    return rewrite(s,((ANALYZE_ROOT,roots),(READ,read)))

def patch_label(s,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
    hits=list(pat.finditer(s))
    if len(hits)!=1:raise ValueError('vector hook')
    pos=hits[0].end()
    return s[:pos]+f'    v1260_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[pos:]

def install(root,v,t,d):
    paths=sorted(root.glob('output_*.cpp'));src={p:p.read_text() for p in paths}
    wanted={a+4*i:(a,w) for a,ws in ((VECTOR,v),(TRAMP,t)) for i,w in enumerate(ws)}
    n=audit_native(src.values(),(root/'main_output.cpp').read_text(),{**wanted,DISPATCH:(DISPATCH,d)})
    if n!=59:raise ValueError('native coverage')
    changes={}
    for p,s in src.items():
        old=s
        for pc,(_,w) in wanted.items():
            if not re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s):continue
            s=patch_label(s,pc,w)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('hook include')
            s=s.replace(a,a+'\nvoid v1260_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
            changes[p]=s
    if sum(s.count('    v1260_before(ctx,') for s in changes.values())!=58:raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print('V1260_VECTOR_TRANSLATION verified=1 vector=38 trampoline=20 dispatcher_entry=1')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--analyzer',action='store_true');m.add_argument('--install',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        dol,elf=a.dol.read_bytes(),a.elf.read_bytes();v,t,d=geometry(dol,elf)
        if a.analyzer:
            a.out.write_text(analyzer(a.out.read_text()));print('V1260_VECTOR_ANALYZER installed=1');return 0
        if a.install:install(a.out,v,t,d);return 0
        image=a.out/'fixture.dol';symbols=a.out/'symbols.csv'
        raw,csv=extend(image.read_bytes(),symbols.read_text(),exact_words(dol,elf,SOURCE,38),data_at(dol,VECTORS,60),t,d)
        with (a.out/'v1260_private_vector.h').open('x') as f:f.write(render(v,t,d))
        image.write_bytes(raw);symbols.write_text(csv)
        print('V1260_VECTOR_FIXTURE accepted=1 native_roots=2 guarded_dispatcher=1')
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1260_VECTOR_PREP accepted=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
