#!/usr/bin/env python3
"""Authenticate original synchronous IOS_Open completion without execution."""
import argparse,struct,re
from pathlib import Path
from make_v651_open_fixture import submit_geometry,SUBMIT,OPEN
from make_v639_open_geometry import geometry as open_geometry
from make_v1243_stm_fixture import seed_data
from prepare_v629_stm_open import geometry as stm_geometry,STM,FIRST_OPEN_CALL
from make_v1252_sleep_fixture import geometry as sleep_geometry,SLEEP
from apply_open_roots_v645 import irq_spans
from make_v624_ipc_geometry import ROOT,exact_words
from prepare_v419_full_start import MAX_DOL,direct_bl,words_at
from prepare_v1281_reply_fixture import symbols
from prepare_v1321_combined_resume import scope as combined_scope
from prepare_v1260_scheduler_vector import SOURCE,SC_SOURCE,VECTORS,BLR
from prepare_v453_debug_leaf import data_at
from make_v626_ipc_fixture import assemble
SECOND=0x8052b0b4
FREE=0x8051ad3c
DISABLE=0x805265ac
RESTORE=0x805265d4

def corridor(root,words,start,stop,target):
    if not root<=start<=stop<root+4*len(words) or (root|start|stop|target)&3:
        raise ValueError('completion corridor')
    if direct_bl(words[(stop-root)//4],stop)!=target:raise ValueError('completion call')
    seen=set();exits=set();work=[start];reached=False
    while work:
        pc=work.pop()
        if pc in seen:continue
        if not root<=pc<=stop:
            exits.add(pc);continue
        seen.add(pc)
        if pc==stop:reached=True;continue
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op in (16,18):
            if w&3:raise ValueError('completion control')
            m,s=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            dst=(pc+((w&m)^s)-s)&0xffffffff
            work.append(dst)
            if op==16 and (w>>21)&20!=20:work.append(pc+4)
        elif op==17 or (op==19 and xo in (16,50,528)) or (op==31 and xo==146):
            raise ValueError('completion control')
        else:work.append(pc+4)
    if not reached:raise ValueError('completion unreachable')
    return tuple(sorted(seen)),tuple(sorted(exits))

def plan(dol,elf):
    bridge,body,_,_,paths,_=stm_geometry(dol,elf)
    sub,edges=submit_geometry(dol,elf)
    _,_,op=open_geometry(dol,elf)
    sleep,sleep_edges,_=sleep_geometry(dol,elf)
    shared={SLEEP:tuple(sleep),SUBMIT:tuple(sub[SUBMIT]),FREE:tuple(sub[FREE]),OPEN:tuple(op[OPEN])}
    shared.update({a:tuple(exact_words(dol,elf,a,n//4)) for a,n in irq_spans(dol,elf)})
    sites=((SLEEP,0x8052a500,RESTORE),(SUBMIT,0x805197dc,RESTORE),(SUBMIT,0x80519804,FREE),
           (FREE,0x8051ad60,DISABLE),(FREE,0x8051af04,RESTORE),(OPEN,0x80519a38,SUBMIT))
    rows=[]
    for owner,pc,dst in sites:
        ws=shared[owner];i=(pc-owner)//4
        if not 0<=i<len(ws) or direct_bl(ws[i],pc)!=dst:raise ValueError('completion edge')
        rows.append((dst,pc+4,ws[i],shared[dst][0]))
    old=tuple(body[:(FIRST_OPEN_CALL-STM)//4+1])
    new=tuple(body[:(SECOND-STM)//4+1])
    if len(old)!=23 or len(new)!=33 or direct_bl(old[-1],FIRST_OPEN_CALL)!=OPEN:raise ValueError('completion prefix')
    visits,exits=corridor(STM,new,FIRST_OPEN_CALL+4,SECOND,OPEN)
    old_data=seed_data(dol,old,paths);data=seed_data(dol,new,paths)
    if any(data.get(a)!=v for a,v in old_data.items()):raise ValueError('completion data')
    return shared,tuple(rows),old,new,visits,exits,data,old_data

def merge(blocks,shared,old,new):
    if len(old)!=23 or len(new)!=33 or tuple(new[:len(old)])!=old or blocks.get(STM)!=old+(BLR,):
        raise ValueError('completion predecessor')
    if any(blocks.get(a)!=ws for a,ws in shared.items()):raise ValueError('completion shared identity')
    out={**blocks,STM:new+(BLR,)}
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in out.items())
    if len(out)+2>48 or any(end>b for (_,end),(b,_) in zip(spans,spans[1:])):raise ValueError('completion ownership')
    return out

def rebuild(raw,expanded):
    table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**expanded,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    image=bytes(out)+table
    if any(words_at(image,a,len(ws))!=ws for a,ws in expanded.items()):raise ValueError('completion roundtrip')
    return image

def verify(dol,elf,raw,csv):
    shared,edges,old,new,visits,exits,data,old_data=plan(dol,elf)
    sizes=symbols(csv)
    blocks={a:words_at(raw,a,n//4) for a,n in sizes.items()}
    expanded=merge(blocks,shared,old,new)
    prior=dict(combined_scope(dol,elf,sizes))
    if STM in prior and prior[STM]!=4*(len(old)+1):raise ValueError('completion ownership')
    prior[STM]=4*(len(new)+1)
    spans=sorted(prior.items())
    if any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):raise ValueError('completion ownership')
    rebuild(raw,expanded)
    print(f'V1337_COMPLETION_PREFLIGHT verified=1 roots={len(expanded)+2} shared_roots={len(shared)} direct_edges={len(edges)+2} stm_original_words={len(new)} continuation_labels={len(visits)} alternate_exits={len(exits)} additional_seed_bytes={len(data)-len(old_data)} original_execution=0')

def install_submit(root,p):
    from prepare_v625_ipc_client import audit_native
    from prepare_v1299_reply_return import verify_resume
    from prepare_owner_scheduler_v722 import reachable
    from prepare_v680_si_helper import verify_direct
    shared,edges,*_=p
    resume=0x805197d8
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in shared.items() if a in (SUBMIT,RESTORE,FREE)
              for pc in reachable(a,ws)}
    sources={f:f.read_text() for f in sorted(root.glob('output_*.cpp'))}
    main=(root/'main_output.cpp').read_text()
    audit_native(sources.values(),main,expected)
    verify_resume(main,((resume,SUBMIT),))
    for dst,lr,_,_ in edges[1:3]:
        owners=[s for s in sources.values() if f'loc_{lr-4:X}: ;' in s]
        if len(owners)!=1:raise ValueError('completion call')
        verify_direct(owners[0],lr-4,dst)
    wanted={pc:w for pc,(a,w) in expected.items() if a==SUBMIT}
    seen=set();changes={}
    for f,s in sources.items():
        old=s
        for pc,w in wanted.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            hits=list(pat.finditer(s))
            if not hits:continue
            if len(hits)!=1 or pc in seen:raise ValueError('completion hook')
            seen.add(pc);i=hits[0].end();s=s[:i]+f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('completion hook')
            changes[f]=s.replace(anchor,anchor+'\nvoid v1344_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if seen!=set(wanted):raise ValueError('completion hook')
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    rows=[(a,a+4*i,w) for a,ws in shared.items() if a in (SUBMIT,RESTORE,FREE) for i,w in enumerate(ws)]
    header='#pragma once\n#include "wii_submit_resume_v1342.h"\nnamespace v1344 {\n'
    header+=f'inline constexpr std::array<undercover::wii::ReplyNativeWord,{len(rows)}> words'+'{'+','.join('undercover::wii::ReplyNativeWord{'+fmt(row)+'}' for row in rows)+'};\n'
    header+='inline constexpr undercover::wii::SubmitResumeExpectation expected{'+fmt((SUBMIT,resume,edges[5][1],edges[5][2]))+','+','.join('undercover::wii::VectorEdge{'+fmt(e)+'}' for e in edges[1:3])+',words};\n}\n'
    with (root.parent/'input'/'v1344_private_submit.h').open('x') as f:f.write(header)
    for f,s in changes.items():f.write_text(s)
    print(f'V1344_SUBMIT_TRANSLATION verified=1 submit_labels={len(wanted)} audited_labels={len(expected)} direct_edges=2')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);p.add_argument('--submit-install',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        if a.submit_install:install_submit(a.out,plan(d,e));return 0
        verify(d,e,(a.out/'fixture.dol').read_bytes(),(a.out/'symbols.csv').read_text());return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed=('size','completion corridor','completion call','completion control','completion unreachable','completion edge','completion prefix','completion data','completion predecessor','completion shared identity','completion ownership','completion roundtrip')
        print('V1337_COMPLETION_PREFLIGHT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
