#!/usr/bin/env python3
"""Authenticate existing nested-wake code and reuse prior native hooks."""
import argparse,re,struct
from pathlib import Path
from prepare_v1289_wake_fixture import plan as wake_plan,WAKE,SELECT,RESTORE,BLR,symbols
from make_v1256_scheduler_fixture import GET
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native

def geometry(p):
    n,g,edges,rp,ep,sn,ss=p
    native={WAKE:n[WAKE],SELECT:sn[SELECT],GET:sn[GET],RESTORE:ep[3][RESTORE]}
    if len(native[WAKE])!=61 or len(native[SELECT])!=138 or len(native[GET])!=3 or any(ws[-1]!=BLR for ws in native.values()):
        raise ValueError('nested extent')
    getter=0x80529744
    gw=native[SELECT][(getter-SELECT)//4]
    if direct_bl(gw,getter)!=GET:raise ValueError('nested getter')
    rows=[x for x in edges if x[0]==RESTORE]
    if len(rows)!=1 or rows[0][1]!=0x8052a5f8 or rows[0][3]!=native[RESTORE][0]:
        raise ValueError('nested restore')
    counter=ep[8]
    if not -32768<=counter<=32767 or counter%4:raise ValueError('nested counter')
    return native,(GET,getter+4,gw,native[GET][0]),rows[0],counter

def verify_fixture(raw,sizes,p):
    for pc,ws in p[0].items():
        if sizes.get(pc)!=4*len(ws) or words_at(raw,pc,len(ws))!=tuple(ws):
            raise ValueError('nested fixture identity')

def render(p):
    native,get,restore,counter=p
    f=lambda n:f'0x{n:08x}u'
    words=[(pc,pc+4*i,w) for pc,ws in sorted(native.items()) for i,w in enumerate(ws)]
    edges=','.join('undercover::wii::VectorEdge{'+','.join(map(f,row))+'}' for row in (get,restore))
    return '\n'.join(('#pragma once','#include "wii_nested_wake_return_v1291.h"','#include <array>','namespace v1292 {',
        'inline constexpr int32_t counter_disp='+str(counter)+';',
        'inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(words))+'> words{'+
        ','.join('undercover::wii::ReplyNativeWord{'+','.join(map(f,row))+'}' for row in words)+'};',
        'inline constexpr undercover::wii::NestedWakeExpectation expected(uint32_t context,uint32_t counter){return {'+
        ','.join(map(f,(WAKE,SELECT,GET,RESTORE)))+',context,counter,'+edges+',words};}','}',''))

def expected_labels(p):
    return {pc:(a,ws[(pc-a)//4]) for a,ws in p[0].items() for pc in reachable(a,ws)}

def verify_hooks(sources,expected):
    for pc,(owner,w) in expected.items():
        name='v1289_before' if owner==WAKE else 'v1270_before'
        pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n'
            +r'    '+name+r'\(ctx,0x'+f'{pc:08x}'+r'u,0x'+f'{w:08x}'+r'u\);$')
        if sum(len(pat.findall(s)) for s in sources)!=1:raise ValueError('nested hook identity')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--audit',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        result=geometry(wake_plan(a.dol.read_bytes(),a.elf.read_bytes()))
        if a.audit:
            sources=[x.read_text() for x in sorted(a.out.glob('output_*.cpp'))]
            labels=expected_labels(result)
            if audit_native(sources,(a.out/'main_output.cpp').read_text(),labels)!=len(labels):
                raise ValueError('nested label coverage')
            verify_hooks(sources,labels)
            print(f'V1292_NESTED_TRANSLATION verified=1 native_labels={len(labels)} reused_hooks=1');return 0
        verify_fixture((a.out/'fixture.dol').read_bytes(),symbols((a.out/'symbols.csv').read_text()),result)
        with (a.out/'v1292_private_nested.h').open('x') as f:f.write(render(result))
        print('V1292_NESTED_FIXTURE accepted=1 additional_roots=0 original_wake=1')
    except (OSError,ValueError,KeyError,IndexError,struct.error) as e:
        allowed=('size','nested extent','nested getter','nested restore','nested counter','nested fixture identity','nested label coverage','nested hook identity')
        reason=str(e) if str(e) in allowed else 'prior_or_io'
        print('V1292_NESTED_PREP accepted=0 reason='+reason.replace(' ','_'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
