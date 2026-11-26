#!/usr/bin/env python3
"""Extend the authenticated native IPC dispatcher through its actual ACK return."""
import argparse,struct,re
from pathlib import Path
from prepare_v1261_ipc_dispatch import geometry as dispatch_geometry,analyzer as dispatch_analyzer
from make_v1255_ack_fixture import geometry as ack_geometry,render as ack_render,IPC,DISPATCH_RETURN,ALLOWED,FORBIDDEN
from make_v624_ipc_geometry import ROOT,exact_words
from prepare_v1260_scheduler_vector import SOURCE,SC_SOURCE,VECTORS,BLR
from prepare_v453_debug_leaf import data_at
from prepare_v419_full_start import words_at,MAX_DOL
from make_v626_ipc_fixture import assemble
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v667_si_dispatch import DISPATCH
from apply_stm_native_open_v632 import OLD as SCANNER
from apply_irq_bootstrap_v475 import rewrite

def geometry(dol,elf):
    g=dispatch_geometry(dol,elf);native,stop,edges,branch=ack_geometry(dol,elf)
    if g[4]!=IPC or g[2]+4!=DISPATCH_RETURN or g[3]!=branch or g[5]!=native[IPC][0]:
        raise ValueError('ACK dispatcher identity')
    ret=exact_words(dol,elf,DISPATCH_RETURN,1)[0]
    return g,native,stop,edges,branch,ret

def extend(raw,csv,g,native,stop,ret):
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if name!=f'func_{pc:08X}' or not size or size%4 or pc in blocks:raise ValueError('symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    if blocks.get(IPC)!=(native[IPC][0],BLR) or blocks.get(DISPATCH)!=tuple(g[0][DISPATCH]):
        raise ValueError('ACK dispatcher predecessor')
    for pc,ws in native.items():
        if pc!=IPC and pc in blocks and tuple(ws)!=blocks[pc]:raise ValueError('ACK shared span')
        blocks[pc]=tuple(ws)
    for pc,ws in stop.items():
        if pc in blocks:raise ValueError('ACK guard overlap')
        blocks[pc]=tuple(ws)+(BLR,)
    d=list(blocks[DISPATCH]);i=(DISPATCH_RETURN-DISPATCH)//4
    if d[i]!=BLR:raise ValueError('ACK return guard')
    d[i]=ret;blocks[DISPATCH]=tuple(d)
    table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**blocks,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return bytes(out)+table,csv

def analyzer(s,g,native,stop):
    # One dispatcher ownership scope, with the handler span expanded.
    roots=dict(g[0]);roots.update(native);roots.update({pc:tuple(ws)+(BLR,) for pc,ws in stop.items()})
    s=dispatch_analyzer(s,(roots,*g[1:]))
    scanner=SCANNER+'\n    if('+'||'.join(f'func.start_address==0x{pc:08x}u' for pc in sorted(set(native)|set(stop)))+')func.hle_hook_name.clear();'
    return rewrite(s,((SCANNER,scanner),))

def render(native,stop,edges,branch,ret):
    return ack_render(native,stop,edges,branch)+f'namespace v1266 {{ inline constexpr uint32_t return_word=0x{ret:08x}u; }}\n'

def install(root,native,stop,edges,ret):
    paths=sorted(root.glob('output_*.cpp'));src={p:p.read_text() for p in paths}
    expected={pc+4*i:(pc,w) for pc,ws in {**native,**stop}.items() for i,w in enumerate(ws)}
    # The restored original dispatcher continuation is never executed;
    # the outer callback stops before dispatching it.
    if audit_native(src.values(),(root/'main_output.cpp').read_text(),expected)!=len(expected):
        raise ValueError('ACK native coverage')
    for pc,lr,_,_ in edges:
        owners=[s for s in src.values() if f'loc_{lr-4:X}: ;' in s]
        if len(owners)!=1:raise ValueError('ACK direct owner')
        verify_direct(owners[0],lr-4,pc)
    seen=set();changes={}
    wanted={pc:w for pc,(_,w) in expected.items()}
    # Also refuse any attempt to execute the continuation before validation.
    wanted[DISPATCH_RETURN]=ret
    for p,s in src.items():
        old=s
        for pc,w in wanted.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('ACK hook identity')
            seen.add(pc);i=m[0].end()
            s=s[:i]+f'    v1266_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('ACK hook include')
            changes[p]=s.replace(a,a+'\nvoid v1266_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if not set(expected)<=seen:raise ValueError('ACK hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V1266_ACK_TRANSLATION verified=1 native_labels={len(expected)} original_return=1')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--analyzer',action='store_true');m.add_argument('--install',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        g,native,stop,edges,branch,ret=geometry(a.dol.read_bytes(),a.elf.read_bytes())
        if a.analyzer:a.out.write_text(analyzer(a.out.read_text(),g,native,stop));print('V1266_ACK_ANALYZER installed=1');return 0
        if a.install:install(a.out,native,stop,edges,ret);return 0
        image=a.out/'fixture.dol';symbols=a.out/'symbols.csv'
        raw,csv=extend(image.read_bytes(),symbols.read_text(),g,native,stop,ret)
        with (a.out/'v1266_private_ack.h').open('x') as f:f.write(render(native,stop,edges,branch,ret))
        image.write_bytes(raw);symbols.write_text(csv)
        print('V1266_ACK_FIXTURE accepted=1 original_handler=1 original_return=1')
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1266_ACK_PREP accepted=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
