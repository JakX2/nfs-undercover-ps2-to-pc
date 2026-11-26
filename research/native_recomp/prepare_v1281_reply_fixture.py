#!/usr/bin/env python3
"""Extend the private joined IRQ fixture to the actual reply wake call."""
import argparse,re,struct
from pathlib import Path
from prepare_v1279_reply_geometry import plan as reply_plan,REPLY,READ as IPC_READ,WRITE as IPC_WRITE,CACHE,WAKE,WAKE_LR
from prepare_v1266_joined_ack import geometry as ack_geometry
from prepare_v1270_ipc_epilogue import geometry as epilogue_geometry,scope as epilogue_scope,analyzer
from make_v1256_scheduler_fixture import geometry as scheduler_geometry
from prepare_v1260_scheduler_vector import SOURCE,SC_SOURCE,VECTORS,BLR
from make_v624_ipc_geometry import ROOT
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at,MAX_DOL
from prepare_v453_debug_leaf import data_at
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct

def plan(dol,elf):
    native,guards,edges,_,_=reply_plan(dol,elf)
    _,ack,_,_,_,_=ack_geometry(dol,elf)
    native={**native,IPC_READ:ack[IPC_READ],IPC_WRITE:ack[IPC_WRITE]}
    return native,guards,edges

def symbols(csv):
    out={}
    rows=csv.splitlines()
    if not rows or rows[0]!='Name,Location,Size':raise ValueError('reply symbols')
    for row in rows[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if name!=f'func_{pc:08X}' or not 4<=size<=4096 or size%4 or pc&3 or pc in out:
            raise ValueError('reply symbols')
        out[pc]=size
    return out

def merge(blocks,native,guards):
    result=dict(blocks)
    if set(native)!={REPLY,IPC_READ,IPC_WRITE,CACHE} or WAKE not in guards or set(native)&set(guards):
        raise ValueError('reply roots')
    if result.get(REPLY)!=(native[REPLY][0],BLR) or CACHE in result:
        raise ValueError('reply predecessor')
    for pc in (IPC_READ,IPC_WRITE):
        if result.get(pc)!=tuple(native[pc]):raise ValueError('reply shared span')
    if result.get(WAKE)!=tuple(guards[WAKE])+(BLR,):raise ValueError('wake predecessor')
    for pc,ws in guards.items():
        if len(ws)!=1:raise ValueError('reply guard')
        if pc in result:
            if result[pc][0]!=ws[0]:raise ValueError('reply guard')
        else:result[pc]=tuple(ws)+(BLR,)
    result.update({pc:tuple(ws) for pc,ws in native.items()})
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in result.items())
    if any(z>y for (_,z),(y,_) in zip(spans,spans[1:])):raise ValueError('reply ownership')
    # Two separately authenticated low-memory vector sources are also
    # counted by the fixture assembler. Never silently raise its cap.
    if len(result)+2>48:raise ValueError('reply root budget')
    return result

def extend(raw,csv,p):
    native,guards,_=p
    blocks={pc:words_at(raw,pc,n//4) for pc,n in symbols(csv).items()}
    blocks=merge(blocks,native,guards)
    table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**blocks,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return bytes(out)+table,csv

def scope(prior,sizes,native,guards):
    spans=dict(prior)
    for pc,ws in native.items():
        n=len(ws)*4
        if sizes.get(pc)!=n or (pc in spans and pc!=REPLY and spans[pc]!=n):
            raise ValueError('reply ownership')
        spans[pc]=n
    for pc in guards:
        n=sizes.get(pc,0)
        if not 8<=n<=4096 or n%4 or (pc in spans and spans[pc]!=n):
            raise ValueError('reply ownership')
        spans[pc]=n
    rows=sorted(spans.items())
    if any(a+n>b for (a,n),(b,_) in zip(rows,rows[1:])):raise ValueError('reply ownership')
    return rows

def render(p):
    native,guards,edges=p
    f=lambda n:f'0x{n:08x}u'
    words=[(pc,pc+4*i,w) for pc,ws in sorted({**native,**guards}.items()) for i,w in enumerate(ws)]
    rows=['#pragma once','#include "wii_reply_processor_v1280.h"','#include <array>','namespace v1281 {']
    rows.append('inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(words))+'> words{'+
        ','.join('undercover::wii::ReplyNativeWord{'+','.join(map(f,x))+'}' for x in words)+'};')
    rows.append('inline constexpr std::array<undercover::wii::VectorEdge,'+str(len(edges))+'> edges{'+
        ','.join('undercover::wii::VectorEdge{'+','.join(map(f,x))+'}' for x in edges)+'};')
    rows.append('inline constexpr undercover::wii::ReplyProcessorExpectation expected(uint32_t context,uint32_t thread){return {'+
        ','.join(map(f,(REPLY,IPC_READ,IPC_WRITE,CACHE,WAKE,WAKE_LR)))+',context,thread,words,edges};}')
    rows.extend(('}',''))
    return '\n'.join(rows)

def install(root,p):
    native,guards,edges=p
    expected={pc+4*i:(pc,w) for pc,ws in {**native,**guards}.items() for i,w in enumerate(ws)}
    src={p:p.read_text() for p in sorted(root.glob('output_*.cpp'))}
    if audit_native(src.values(),(root/'main_output.cpp').read_text(),expected)!=len(expected):
        raise ValueError('reply native coverage')
    for dst,lr,_,_ in edges:
        owners=[s for s in src.values() if f'loc_{lr-4:X}: ;' in s]
        if len(owners)!=1:raise ValueError('reply native owner')
        verify_direct(owners[0],lr-4,dst)
    wanted={pc:w for pc,(owner,w) in expected.items() if owner in native}
    seen=set();changes={}
    for p,s in src.items():
        old=s
        for pc,w in wanted.items():
            pattern=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            matches=list(pattern.finditer(s))
            if not matches:continue
            if len(matches)!=1 or pc in seen:raise ValueError('reply hook identity')
            seen.add(pc);i=matches[0].end()
            s=s[:i]+f'    v1281_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[i:]
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('reply hook include')
            changes[p]=s.replace(anchor,anchor+'\nvoid v1281_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if seen!=set(wanted):raise ValueError('reply hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V1281_REPLY_TRANSLATION verified=1 native_labels={len(expected)} original_body=1 cache=1 wake_executed=0')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--analyzer',action='store_true');m.add_argument('--install',action='store_true')
    p.add_argument('--symbols',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        dol,elf=a.dol.read_bytes(),a.elf.read_bytes();result=plan(dol,elf)
        if a.analyzer:
            if a.symbols is None:raise ValueError('reply symbols')
            ep=epilogue_geometry(dol,elf);sn,ss,*_=scheduler_geometry(dol,elf)
            spans=scope(epilogue_scope(ep,sn,ss),symbols(a.symbols.read_text()),result[0],result[1])
            a.out.write_text(analyzer(a.out.read_text(),spans))
            print('V1281_REPLY_ANALYZER installed=1');return 0
        if a.install:install(a.out,result);return 0
        image=a.out/'fixture.dol';csv=a.out/'symbols.csv'
        raw,rows=extend(image.read_bytes(),csv.read_text(),result)
        with (a.out/'v1281_private_reply.h').open('x') as f:f.write(render(result))
        image.write_bytes(raw);csv.write_text(rows)
        print(f'V1281_REPLY_FIXTURE accepted=1 roots={len(symbols(rows))} original_body=1 cache=1 wake_guard=1')
    except (OSError,ValueError,KeyError,IndexError,struct.error) as e:
        allowed=('size','reply symbols','reply roots','reply predecessor','reply shared span','wake predecessor',
                 'reply guard','reply ownership','reply root budget','reply native coverage','reply native owner',
                 'reply hook identity','reply hook include','reply hook coverage')
        reason=str(e) if str(e) in allowed else 'prior_or_io'
        print('V1281_REPLY_PREP accepted=0 reason='+reason.replace(' ','_'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
