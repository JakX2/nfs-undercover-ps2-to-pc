#!/usr/bin/env python3
"""Authenticate existing private native labels for the post-wake reply return."""
import argparse,re,struct
from pathlib import Path
from prepare_v1281_reply_fixture import plan as reply_plan
from prepare_v1266_joined_ack import geometry as ack_geometry,IPC
from prepare_v1279_reply_geometry import REPLY,READ,WRITE,WAKE,WAKE_LR,REPLY_LR,BLR
from make_v1255_ack_fixture import DISPATCH_RETURN
from prepare_v419_full_start import MAX_DOL,direct_bl,words_at
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct

def plan(dol,elf):
    native,_,edges=reply_plan(dol,elf)
    _,ack,_,ack_edges,_,_=ack_geometry(dol,elf)
    roots={REPLY:native[REPLY],IPC:ack[IPC],READ:native[READ],WRITE:native[WRITE]}
    if any(not ws or ws[-1]!=BLR for ws in roots.values()):
        raise ValueError('return extent')
    if any(tuple(roots[pc])!=tuple(ack[pc]) for pc in (READ,WRITE)):
        raise ValueError('return shared leaf')
    for owner,site,dst in ((REPLY,WAKE_LR-4,WAKE),(IPC,REPLY_LR-4,REPLY)):
        i=(site-owner)//4
        if not 0<=i<len(roots[owner])-1 or direct_bl(roots[owner][i],site)!=dst:
            raise ValueError('return predecessor')
    rows=tuple(row for row in (*edges,*ack_edges) if row[0] in (READ,WRITE))
    if not rows or len(set(rows))!=len(rows) or len(rows)>64:
        raise ValueError('return edges')
    for dst,lr,w,entry in rows:
        owner=REPLY if REPLY<=lr-4<REPLY+4*len(roots[REPLY]) else IPC
        i=(lr-4-owner)//4
        if not 0<=i<len(roots[owner]) or roots[owner][i]!=w or direct_bl(w,lr-4)!=dst or roots[dst][0]!=entry:
            raise ValueError('return edges')
    return roots,rows

def labels(p):
    out={}
    for owner,ws in p[0].items():
        for i,w in enumerate(ws):
            pc=owner+4*i
            if pc in out:raise ValueError('return ownership')
            out[pc]=(owner,w)
    return out

def render(p):
    f=lambda n:f'0x{n:08x}u'
    rows=labels(p)
    words=','.join('undercover::wii::ReplyNativeWord{'+','.join(map(f,(a,pc,w)))+'}' for pc,(a,w) in sorted(rows.items()))
    edges=','.join('undercover::wii::VectorEdge{'+','.join(map(f,x))+'}' for x in p[1])
    return '\n'.join(('#pragma once','#include "wii_reply_return_v1298.h"','#include <array>','namespace v1299 {',
        f'inline constexpr std::array<undercover::wii::ReplyNativeWord,{len(rows)}> words'+'{'+words+'};',
        f'inline constexpr std::array<undercover::wii::VectorEdge,{len(p[1])}> edges'+'{'+edges+'};',
        'inline constexpr undercover::wii::ReplyReturnExpectation expected(uint32_t counter){return {'+
        ','.join(map(f,(REPLY,IPC,READ,WRITE,WAKE_LR,REPLY_LR,DISPATCH_RETURN)))+',counter,words,edges,true};}','}',''))

def verify_hooks(sources,expected):
    for pc,(owner,w) in expected.items():
        name='v1266_before' if owner==IPC else 'v1281_before'
        # The reply hook is installed after the ACK hook and therefore
        # precedes it at shared leaves. Only that first hook owns the word.
        pattern=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n'
            +r'    '+name+r'\(ctx,0x'+f'{pc:08x}'+r'u,0x'+f'{w:08x}'+r'u\);$')
        if sum(len(pattern.findall(s)) for s in sources)!=1:
            raise ValueError('return hook identity')

def verify_resume(main,rows):
    for pc,owner in rows:
        pattern=re.compile(r'(?mi)^[ \t]*case[ \t]+0x'+f'{pc:X}'+r'[ \t]*:[ \t]*([^\r\n]*)')
        hits=pattern.findall(main)
        if len(hits)!=1 or not re.fullmatch(f'func_{owner:08X}'+r'\(ctx\);[ \t]*break;[ \t]*',hits[0],re.I):
            raise ValueError('return dispatch identity')

def verify_fixture(raw,sizes,p):
    for pc,ws in p[0].items():
        if sizes.get(pc)!=4*len(ws) or words_at(raw,pc,len(ws))!=tuple(ws):
            raise ValueError('return fixture identity')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--audit',action='store_true');a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:
            raise ValueError('size')
        result=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.audit:
            src=[x.read_text() for x in sorted(a.out.glob('output_*.cpp'))]
            main=(a.out/'main_output.cpp').read_text();expected=labels(result)
            if audit_native(src,main,expected)!=len(expected):raise ValueError('return native coverage')
            verify_hooks(src,expected);verify_resume(main,((WAKE_LR,REPLY),(REPLY_LR,IPC)))
            for dst,lr,_,_ in result[1]:
                owners=[s for s in src if f'loc_{lr-4:X}: ;' in s]
                if len(owners)!=1:raise ValueError('return edge owner')
                verify_direct(owners[0],lr-4,dst)
            print(f'V1299_REPLY_RETURN_TRANSLATION verified=1 native_labels={len(expected)} reused_hooks=1 resume_cases=2');return 0
        from prepare_v1281_reply_fixture import symbols
        verify_fixture((a.out/'fixture.dol').read_bytes(),symbols((a.out/'symbols.csv').read_text()),result)
        with (a.out/'v1299_private_return.h').open('x') as f:f.write(render(result))
        print('V1299_REPLY_RETURN_FIXTURE accepted=1 additional_roots=0');return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as e:
        allowed=('size','return extent','return shared leaf','return predecessor','return edges','return ownership',
                 'return hook identity','return dispatch identity','return fixture identity','return native coverage','return edge owner')
        reason=str(e) if str(e) in allowed else 'prior_or_io'
        print('V1299_REPLY_RETURN_PREP accepted=0 reason='+reason.replace(' ','_'));return 1
if __name__=='__main__':raise SystemExit(main())
