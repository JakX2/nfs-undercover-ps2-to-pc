#!/usr/bin/env python3
"""Extend the private vector fixture through the original IPC dispatcher prefix."""
import argparse,re,struct
from pathlib import Path
from prepare_owner_second_dispatch_v946 import plan as prior,reachable
from prepare_owner_scheduler_v722 import sda_accesses
from prepare_v667_si_dispatch import DISPATCH,SCHED,TIME,DISABLE,RESTORE,HANDLER as SI
from make_v624_ipc_geometry import ROOT,exact_words,geometry as ipc_geometry
from make_v626_ipc_fixture import assemble
from prepare_v1260_scheduler_vector import VECTOR,TRAMP,SOURCE,SC_SOURCE,VECTORS,BLR,analyzer as vector_analyzer
from prepare_v419_full_start import MAX_DOL,words_at
from prepare_v453_debug_leaf import data_at
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from apply_bat_roots_v586 import ROOT as ANALYZE_ROOT,READ
from apply_irq_bootstrap_v475 import rewrite

def geometry(dol,elf):
    roots,edges,indirect,iw,_,dw,guard=prior(dol,elf)
    _,handler,hw,_=ipc_geometry(dol,elf)
    if handler==SI or handler in roots:raise ValueError('IPC target')
    roots=dict(roots);del roots[SI];roots[handler]=[hw,BLR]
    guard=(set(guard)-{SI,SI+4})|{handler,handler+4}
    reads=sda_accesses(roots[SCHED],32);writes=sda_accesses(roots[SCHED],36)
    if len(reads)!=1 or reads!=writes:raise ValueError('scheduler counter')
    # Shared disable/restore functions must remain wholly original.
    for pc in (DISABLE,RESTORE):
        if tuple(roots[pc])!=exact_words(dol,elf,pc,len(roots[pc])):raise ValueError('shared leaf')
    return roots,edges,indirect,iw,handler,hw,dw,guard,reads[0]

def extend(raw,csv,roots):
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if name!=f'func_{pc:08X}' or not size or size%4 or pc in blocks:raise ValueError('symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    if DISPATCH not in blocks or blocks[DISPATCH]!=(roots[DISPATCH][0],BLR) or TRAMP not in blocks:
        raise ValueError('dispatcher predecessor')
    for pc,ws in roots.items():
        if pc!=DISPATCH and pc in blocks and tuple(ws)!=blocks[pc]:raise ValueError('shared span')
        blocks[pc]=tuple(ws)
    table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**blocks,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return bytes(out)+table,csv

def render(g):
    roots,edges,indirect,iw,handler,hw,dw,guard,counter=g
    f=lambda row:','.join(f'0x{x:08x}u' for x in row)
    words=[(a+4*i,w) for a,ws in sorted(roots.items()) for i,w in enumerate(ws)]
    return ('#pragma once\n#include "wii_ipc_dispatch_v1261.h"\nnamespace v1261 {\n'
        'inline constexpr undercover::wii::SiDispatchExpectations code{{'+','.join('undercover::wii::SiDispatchEdge{'+f(e)+'}' for e in edges)+'},'+f((indirect,iw,hw,dw))+'};\n'
        f'inline constexpr uint32_t handler=0x{handler:08x}u;\ninline constexpr int32_t counter_disp={counter};\n'
        'struct Word{uint32_t pc,word;};\ninline constexpr std::array<Word,'+str(len(words))+'> words{'+','.join('Word{'+f(row)+'}' for row in words)+'};\n'
        'inline constexpr std::array<uint32_t,'+str(len(guard))+'> guard{'+f(sorted(guard))+'};\n}\n')

def analyzer(s,g):
    roots=g[0]
    if len(roots[DISPATCH])*4!=0x2a4:raise ValueError('dispatcher extent')
    spans=[(VECTOR,152),(TRAMP,80)]+[(pc,len(ws)*4) for pc,ws in roots.items() if pc not in (DISABLE,RESTORE)]
    root=(ANALYZE_ROOT+'\n    const auto ipc_dispatch_owner=[](uint32_t a)->uint32_t {\n'+''.join(
        f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in spans)+
        '      return 0;\n    };\n    if(ipc_dispatch_owner(func_start)&&ipc_dispatch_owner(func_start)!=func_start)continue;')
    read='        const auto ipc_dispatch_root=ipc_dispatch_owner(current_pc);\n        if((ipc_dispatch_root&&ipc_dispatch_root!=func_start)||(ipc_dispatch_owner(func_start)&&ipc_dispatch_root!=func_start))break;\n'+READ
    return rewrite(s,((ANALYZE_ROOT,root),(READ,read)))

def install(root,g):
    roots,edges,indirect,iw,handler,hw,dw,guard,counter=g
    paths=sorted(root.glob('output_*.cpp'));src={p:p.read_text() for p in paths}
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws,guard,indirect)}
    n=audit_native(src.values(),(root/'main_output.cpp').read_text(),expected)
    if n!=len(expected):raise ValueError('native coverage')
    for pc,lr,_,_ in edges:
        owners=[s for s in src.values() if f'loc_{lr-4:X}: ;' in s]
        if len(owners)!=1:raise ValueError('direct owner')
        verify_direct(owners[0],lr-4,pc)
    wanted={pc:w for pc,(a,w) in expected.items() if a!=handler}
    seen=set();changes={}
    for p,s in src.items():
        old=s
        for pc,w in wanted.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);i=m[0].end()
            s=s[:i]+f'    v1261_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('hook include')
            changes[p]=s.replace(a,a+'\nvoid v1261_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if seen!=set(wanted):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V1261_DISPATCH_TRANSLATION verified=1 native_labels={n} direct_edges=4 indirect=1')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--analyzer',action='store_true');m.add_argument('--install',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        g=geometry(a.dol.read_bytes(),a.elf.read_bytes())
        if a.analyzer:a.out.write_text(analyzer(a.out.read_text(),g));print('V1261_DISPATCH_ANALYZER installed=1');return 0
        if a.install:install(a.out,g);return 0
        image=a.out/'fixture.dol';symbols=a.out/'symbols.csv'
        raw,csv=extend(image.read_bytes(),symbols.read_text(),g[0])
        with (a.out/'v1261_private_dispatch.h').open('x') as f:f.write(render(g))
        image.write_bytes(raw);symbols.write_text(csv);print('V1261_DISPATCH_FIXTURE accepted=1 guarded_prefix=1')
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1261_DISPATCH_PREP accepted=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
