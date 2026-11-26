#!/usr/bin/env python3
"""Expand only the original post-X2 synchronous helper; private output."""
import argparse,re,struct
from pathlib import Path
from prepare_v1279_reply_geometry import REPLY,plan as reply_plan
from prepare_v1289_wake_fixture import plan as wake_plan,scope as wake_scope
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v1281_reply_fixture import symbols
from prepare_v1260_scheduler_vector import SOURCE,SC_SOURCE,VECTORS,BLR
from make_v624_ipc_geometry import ROOT,exact_words
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v453_debug_leaf import data_at
from make_private_elf_symbol_map import parse_functions
from prepare_v1307_cooperative_fixture import leaf_shape
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
HELPER=0x8051b070
HELPER_RETURN=0x805192f8

def helper_plan(dol,elf):
    n=parse_functions(elf).get(HELPER,0)
    if n!=0x7c:raise ValueError('helper extent')
    body=tuple(exact_words(dol,elf,HELPER,n//4))
    leaf_shape(HELPER,body)
    _,guards,edges,_,_=reply_plan(dol,elf)
    if guards.get(HELPER)!=(body[0],) or sum(dst==HELPER and lr==HELPER_RETURN and entry==body[0] and direct_bl(w,lr-4)==dst for dst,lr,w,entry in edges)!=1:
        raise ValueError('helper predecessor')
    return body

def merge(blocks,body):
    if blocks.get(HELPER)!=(body[0],BLR):raise ValueError('helper predecessor')
    out={**blocks,HELPER:body}
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in out.items())
    if len(out)+2>48 or any(end>b for (_,end),(b,_) in zip(spans,spans[1:])):raise ValueError('helper ownership')
    return out

def extend(raw,csv,body):
    blocks=merge({pc:words_at(raw,pc,n//4) for pc,n in symbols(csv).items()},body)
    table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**blocks,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return bytes(out)+table,csv

def scope(dol,elf,sizes):
    prior=dict(wake_scope(wake_plan(dol,elf),{**sizes,HELPER:8}))
    if prior.get(HELPER)!=8 or sizes.get(HELPER)!=0x7c:raise ValueError('helper ownership')
    prior[HELPER]=sizes[HELPER];spans=sorted(prior.items())
    if any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):raise ValueError('helper ownership')
    return spans

def install(root,body):
    expected={HELPER+4*i:(HELPER,w) for i,w in enumerate(body)}
    sources={p:p.read_text() for p in sorted(root.glob('output_*.cpp'))}
    if audit_native(sources.values(),(root/'main_output.cpp').read_text(),expected)!=len(expected):raise ValueError('helper native coverage')
    owners=[s for s in sources.values() if f'loc_{HELPER_RETURN-4:X}: ;' in s]
    if len(owners)!=1:raise ValueError('helper native edge')
    verify_direct(owners[0],HELPER_RETURN-4,HELPER)
    seen=set();changes={}
    for path,source in sources.items():
        s=source
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pat.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('helper hook identity')
            seen.add(pc);i=hits[0].end();s=s[:i]+f'    v1316_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=source:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('helper hook include')
            changes[path]=s.replace(anchor,anchor+'\nvoid v1316_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if seen!=set(expected):raise ValueError('helper hook coverage')
    for path,s in changes.items():path.write_text(s)
    print(f'V1316_HELPER_TRANSLATION verified=1 native_labels={len(expected)} direct_edge=1')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--analyzer',action='store_true');m.add_argument('--install',action='store_true')
    p.add_argument('--symbols',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes();body=helper_plan(d,e)
        if a.analyzer:
            if a.symbols is None:raise ValueError('helper ownership')
            a.out.write_text(analyzer(a.out.read_text(),scope(d,e,symbols(a.symbols.read_text()))))
            print('V1316_HELPER_ANALYZER verified=1');return 0
        if a.install:install(a.out,body);return 0
        image=a.out/'fixture.dol';csv=a.out/'symbols.csv'
        raw,rows=extend(image.read_bytes(),csv.read_text(),body)
        image.write_bytes(raw);csv.write_text(rows)
        print('V1316_HELPER_FIXTURE verified=1 expanded_roots=1 additional_roots=0');return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('size','helper extent','clear extent','clear control','helper predecessor','helper ownership',
            'helper native coverage','helper native edge','helper hook identity','helper hook include','helper hook coverage')
        print('V1316_HELPER_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
