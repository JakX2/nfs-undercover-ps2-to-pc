#!/usr/bin/env python3
"""Private original wake fixture; stop at original scheduler selection."""
import argparse,re,struct
from pathlib import Path
from prepare_v1281_reply_fixture import plan as reply_plan,scope as reply_scope,symbols,WAKE,BLR
from prepare_v1270_ipc_epilogue import geometry as epilogue_geometry,scope as epilogue_scope,analyzer,DISABLE,RESTORE,SELECT
from make_v1256_scheduler_fixture import geometry as scheduler_geometry
from prepare_v1260_scheduler_vector import SOURCE,SC_SOURCE,VECTORS
from make_v624_ipc_geometry import ROOT,exact_words
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at,MAX_DOL,direct_bl
from prepare_v453_debug_leaf import data_at
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_owner_scheduler_v722 import reachable
from make_private_elf_symbol_map import parse_functions
from audit_handler_suffix_v728 import target

EDGES=((WAKE+0x18,DISABLE),(WAKE+0xd0,SELECT),(WAKE+0xd8,RESTORE))
def shape(body):
    if len(body)!=0xf4//4 or body[-1]!=BLR:raise ValueError('wake extent')
    edges=[]
    for i,w in enumerate(body):
        pc=WAKE+4*i;op=w>>26;xo=(w>>1)&1023
        if op==18 and w&1:
            if w&2:raise ValueError('wake control')
            edges.append((pc,direct_bl(w,pc)))
        elif op in (16,18):
            if w&3 or not WAKE<=target(pc,w)<WAKE+4*len(body):raise ValueError('wake control')
        elif op==17 or op==19 and xo in (50,528) or op==31 and xo==146:
            raise ValueError('wake control')
    if tuple(edges)!=EDGES:raise ValueError('wake edges')
    return tuple(edges)

def plan(dol,elf):
    rp=reply_plan(dol,elf);ep=epilogue_geometry(dol,elf);sn,ss,*_=scheduler_geometry(dol,elf)
    if parse_functions(elf).get(WAKE)!=0xf4:raise ValueError('wake extent')
    body=exact_words(dol,elf,WAKE,0xf4//4)
    if rp[1].get(WAKE)!=(body[0],):raise ValueError('wake predecessor')
    edges=shape(body);native={WAKE:body,DISABLE:ep[3][DISABLE]}
    guards={SELECT:(sn[SELECT][0],),RESTORE:(ep[3][RESTORE][0],)}
    rows=tuple((dst,pc+4,body[(pc-WAKE)//4],(native if dst in native else guards)[dst][0]) for pc,dst in edges)
    return native,guards,rows,rp,ep,sn,ss

def merge(blocks,native,guards):
    if set(native)!={WAKE,DISABLE} or set(guards)!={SELECT,RESTORE}:raise ValueError('wake roots')
    if blocks.get(WAKE)!=(native[WAKE][0],BLR) or blocks.get(DISABLE)!=tuple(native[DISABLE]):
        raise ValueError('wake predecessor')
    for pc,ws in guards.items():
        if pc not in blocks or blocks[pc][0]!=ws[0]:raise ValueError('wake shared span')
    out={**blocks,WAKE:tuple(native[WAKE])}
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in out.items())
    if any(end>pc for (_,end),(pc,_) in zip(spans,spans[1:])):raise ValueError('wake ownership')
    return out

def extend(raw,csv,p):
    n,g,*_=p
    blocks={pc:words_at(raw,pc,size//4) for pc,size in symbols(csv).items()}
    blocks=merge(blocks,n,g)
    table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**blocks,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return bytes(out)+table,csv

def scope(p,sizes):
    native,guards,_,rp,ep,sn,ss=p
    if sizes.get(WAKE)!=4*len(native[WAKE]):raise ValueError('wake ownership')
    prior=reply_scope(epilogue_scope(ep,sn,ss),{**sizes,WAKE:8},rp[0],rp[1])
    spans=sorted({**dict(prior),WAKE:sizes[WAKE]}.items())
    if any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):raise ValueError('wake ownership')
    return spans

def render(p):
    native,guards,edges,*_=p
    f=lambda n:f'0x{n:08x}u'
    words=[(pc,pc+4*i,w) for pc,ws in sorted({**native,**guards}.items()) for i,w in enumerate(ws)]
    return '\n'.join(('#pragma once','#include "wii_wake_ready_v1288.h"','#include <array>','namespace v1289 {',
        'inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(words))+'> words{'+
        ','.join('undercover::wii::ReplyNativeWord{'+','.join(map(f,row))+'}' for row in words)+'};',
        'inline constexpr undercover::wii::WakeReadyExpectation expected(uint32_t context,uint32_t thread){return {'+
        ','.join(map(f,(WAKE,DISABLE,SELECT)))+',context,thread,'+
        ','.join('undercover::wii::VectorEdge{'+','.join(map(f,row))+'}' for row in edges[:2])+',words};}','}',''))

def install(root,p):
    native,guards,edges,*_=p
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in native.items() for pc in reachable(a,ws)}
    expected.update({pc:(pc,ws[0]) for pc,ws in guards.items()})
    src={p:p.read_text() for p in sorted(root.glob('output_*.cpp'))}
    if audit_native(src.values(),(root/'main_output.cpp').read_text(),expected)!=len(expected):
        raise ValueError('wake native coverage')
    for dst,lr,_,_ in edges:
        owners=[s for s in src.values() if f'loc_{lr-4:X}: ;' in s]
        if len(owners)!=1:raise ValueError('wake native owner')
        verify_direct(owners[0],lr-4,dst)
    wanted={pc:w for pc,(owner,w) in expected.items() if owner in native}
    seen=set();changes={}
    for p,s in src.items():
        old=s
        for pc,w in wanted.items():
            pattern=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pattern.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('wake hook identity')
            seen.add(pc);i=hits[0].end()
            s=s[:i]+f'    v1289_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('wake hook include')
            changes[p]=s.replace(anchor,anchor+'\nvoid v1289_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if seen!=set(wanted):raise ValueError('wake hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V1289_WAKE_TRANSLATION verified=1 native_labels={len(expected)} direct_edges=3 select_executed=0')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--analyzer',action='store_true');m.add_argument('--install',action='store_true')
    p.add_argument('--symbols',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.analyzer:
            if a.symbols is None:raise ValueError('wake symbols')
            a.out.write_text(analyzer(a.out.read_text(),scope(p,symbols(a.symbols.read_text()))))
            print('V1289_WAKE_ANALYZER installed=1');return 0
        if a.install:install(a.out,p);return 0
        image=a.out/'fixture.dol';csv=a.out/'symbols.csv'
        raw,rows=extend(image.read_bytes(),csv.read_text(),p)
        with (a.out/'v1289_private_wake.h').open('x') as f:f.write(render(p))
        image.write_bytes(raw);csv.write_text(rows)
        print('V1289_WAKE_FIXTURE accepted=1 original_wake=1 select_guard=1')
    except (OSError,ValueError,KeyError,IndexError,struct.error) as e:
        allowed=('size','wake extent','wake control','wake edges','wake predecessor','wake roots','wake shared span',
            'wake ownership','wake native coverage','wake native owner','wake hook identity','wake hook include','wake hook coverage','wake symbols')
        reason=str(e) if str(e) in allowed else 'prior_or_io'
        print('V1289_WAKE_PREP accepted=0 reason='+reason.replace(' ','_'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
