#!/usr/bin/env python3
"""Join the authenticated reply-helper and cooperative context-clear scopes.
Keep all private code/headers in the caller's temporary owner workspace.
"""
import argparse,struct
from pathlib import Path
from prepare_v1307_cooperative_fixture import (CLEAR,SAVE_RETURN,SLEEP_RETURN,plan as cooperative_plan,
    merge as cooperative_merge,extend as cooperative_extend,audit as cooperative_audit)
from prepare_v1316_reply_helper import HELPER,helper_plan,scope as helper_scope
from prepare_v1270_ipc_epilogue import analyzer,L
from prepare_v1314_save_lane import plan as save_plan
from prepare_v1281_reply_fixture import symbols
from prepare_v419_full_start import MAX_DOL,words_at
from make_v1256_scheduler_fixture import geometry as scheduler_geometry,SELECT,CALLBACK,CALLBACK_PTR
from prepare_v625_ipc_client import audit_native
from prepare_v1299_reply_return import verify_resume
from prepare_owner_scheduler_v722 import reachable

def expand_scope(prior,sizes):
    out=dict(prior)
    if out.get(CLEAR)!=8 or out.get(HELPER)!=0x7c or sizes.get(CLEAR)!=0x24 or sizes.get(HELPER)!=0x7c:
        raise ValueError('combined guard scope')
    out[CLEAR]=sizes[CLEAR]
    spans=sorted(out.items())
    if any(n<=0 or n%4 or pc&3 for pc,n in spans) or any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):
        raise ValueError('combined ownership')
    return spans

def merge(blocks,roots,helper):
    if len(helper)!=31 or blocks.get(HELPER)!=helper or HELPER in roots:
        raise ValueError('combined helper identity')
    out=cooperative_merge(blocks,roots)
    if out.get(HELPER)!=helper or set(out)!=set(blocks) or any(out[pc]!=ws for pc,ws in blocks.items() if pc!=CLEAR):
        raise ValueError('combined root identity')
    return out

def plan(dol,elf):
    coop=cooperative_plan(dol,elf)
    helper=helper_plan(dol,elf)
    save=save_plan(dol,elf)
    sn,_,edges,indirect,_=scheduler_geometry(dol,elf)
    if save[2]!=coop[3] or len(sn[CALLBACK])!=1 or not 1<=len(indirect)<=4:
        raise ValueError('combined GQR or callback identity')
    wanted=(0x80529874,0x8052988c,0x8052991c,0x80529924)
    selection=tuple(next((e for e in edges if e[1]==lr),()) for lr in wanted)
    if any(not e for e in selection) or any(e[0]!=CALLBACK for e in indirect):
        raise ValueError('combined selection edges')
    return coop,helper,selection,indirect,sn[CALLBACK]

def ram_rows(roots,callback):
    spans={**roots,CALLBACK:tuple(callback)}
    return tuple((owner,owner+4*i,w) for owner,ws in sorted(spans.items()) for i,w in enumerate(ws))

def render(result):
    coop,_,selection,indirect,callback=result
    roots,_,_,mask=coop
    f=lambda n:f'0x{n:08x}u'
    row=lambda e:'undercover::wii::VectorEdge{'+','.join(map(f,e))+'}'
    loader=roots[L]
    rows=ram_rows(roots,callback)
    return '\n'.join(('#pragma once','#include "wii_idle_selection_v1319.h"','#include "wii_cooperative_load_lane_v1317.h"','#include "wii_private_expansion_seed_v1323.h"','#include <array>','namespace v1321 {',
        f'inline constexpr std::array<undercover::wii::ReplyNativeWord,{len(rows)}> ram_words'+'{'+','.join('undercover::wii::ReplyNativeWord{'+','.join(map(f,row))+'}' for row in rows)+'};',
        'inline constexpr uint32_t clear_root='+f(CLEAR)+';',
        f'inline constexpr std::array<uint32_t,{len(loader)}> loader_words'+'{'+','.join(map(f,loader))+'};',
        f'inline constexpr std::array<undercover::wii::VectorEdge,{len(indirect)}> callbacks'+'{'+','.join(map(row,indirect))+'};',
        'inline constexpr undercover::wii::IdleSelectionExpectation selection(uint32_t thread,uint32_t idle,uint32_t counter){return {thread,idle,counter,'+
        f(CALLBACK_PTR)+','+f(CALLBACK)+','+','.join(map(row,selection))+',callbacks};}',
        'inline constexpr undercover::wii::CooperativeLoadLane::Expectation load(){return {loader_words,'+f(selection[3][1])+','+str(mask)+'u};}',
        '}',''))

def prepare(raw,csv,result):
    coop,helper,*_=result
    blocks={pc:words_at(raw,pc,n//4) for pc,n in symbols(csv).items()}
    merged=merge(blocks,coop[0],helper)
    new,rows=cooperative_extend(raw,csv,coop)
    sizes=symbols(rows)
    if set(sizes)!=set(merged) or any(sizes[pc]!=4*len(ws) or words_at(new,pc,len(ws))!=ws for pc,ws in merged.items()):
        raise ValueError('combined fixture roundtrip')
    return new,rows

def scope(dol,elf,sizes):
    return expand_scope(helper_scope(dol,elf,{**sizes,CLEAR:8}),sizes)

def audit(src,main,result):
    coop,helper,_,_,callback=result
    n=cooperative_audit(src,main,coop)
    expected={HELPER+4*i:(HELPER,w) for i,w in enumerate(helper)}
    expected[CALLBACK]=(CALLBACK,callback[0])
    if audit_native(src,main,expected)!=len(expected):
        raise ValueError('combined native identity')
    return n+len(expected)

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--audit',action='store_true');m.add_argument('--analyzer',action='store_true')
    p.add_argument('--symbols',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes();result=plan(d,e)
        if a.analyzer:
            if a.symbols is None:raise ValueError('combined guard scope')
            a.out.write_text(analyzer(a.out.read_text(),scope(d,e,symbols(a.symbols.read_text()))))
            print('V1321_COMBINED_ANALYZER verified=1 expanded_guards=2');return 0
        if a.audit:
            n=audit([x.read_text() for x in sorted(a.out.glob('output_*.cpp'))],(a.out/'main_output.cpp').read_text(),result)
            print(f'V1321_COMBINED_TRANSLATION verified=1 native_labels={n} expanded_guards=2');return 0
        image=a.out/'fixture.dol';csv=a.out/'symbols.csv'
        raw,rows=prepare(image.read_bytes(),csv.read_text(),result)
        with (a.out/'v1321_private_selection.h').open('x') as f:f.write(render(result))
        image.write_bytes(raw);csv.write_text(rows)
        print('V1321_COMBINED_FIXTURE verified=1 expanded_guards=2 additional_roots=0');return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('size','combined guard scope','combined ownership','combined helper identity','combined root identity',
            'combined GQR or callback identity','combined selection edges','combined fixture roundtrip','combined native identity')
        print('V1321_COMBINED_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
