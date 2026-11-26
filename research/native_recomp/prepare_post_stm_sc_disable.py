#!/usr/bin/env python3
"""Authenticate the shared original interrupt-disable leaf and next SC decision."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_join import plan as entry_plan,ROOT,EDGES
from prepare_v1337_open_completion import plan as completion,DISABLE
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS
from prepare_stm_event_return_geometry import object_at
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import first_region,category
from prepare_owner_scheduler_v722 import reachable
from restore_post_stm_v89 import SIZE
from prepare_ipc_dispatch_geometry import credit_object
from prepare_ipc_profile_geometry import layout
from prepare_v1414_ipc_ring import ring_object
from prepare_stm_event_return_geometry import plan as event_plan
from prepare_stm_final_return import plan as final_plan
from prepare_v625_ipc_client import audit_native
BLR=0x4e800020

def leaf(words):
    if not 3<=len(words)<=12 or words[-1]!=BLR or words.count(BLR)!=1:
        raise ValueError('disable extent')
    mf=mt=0
    for w in words[:-1]:
        op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31
        if op==31 and xo==83 and rs in (0,*range(3,13)):mf+=1
        elif op==31 and xo==146 and rs in (0,*range(3,13)):mt+=1
        elif w in (0x4c00012c,0x7c0004ac):pass
        elif op in (21,24,25) and not(w&1 and op==21) and ra in (0,*range(3,13)):pass
        elif op==14 and rs in (0,*range(3,13)):pass
        elif op==31 and xo in (28,60,444) and not w&1 and ra in (0,*range(3,13)):pass
        else:raise ValueError('disable opcode')
    if mf!=1 or mt!=1:raise ValueError('disable MSR count')
    return len(words)

def leaf_plan(d,e):
    fields,_,_,_=entry_plan(d,e)
    shared,*_=completion(d,e)
    ws=shared[DISABLE]
    if fields[2]!=DISABLE or fields[3]!=ws[0] or len(reachable(DISABLE,ws))!=len(ws):
        raise ValueError('disable identity')
    leaf(ws)
    caller=EDGES[0][0]+4
    return (DISABLE,caller,exact_words(d,e,caller,1)[0]),tuple(ws)

def decision(d,e):
    caller=EDGES[0][0]+4
    body=exact_words(d,e,ROOT,SIZE//4)
    rows,backs,stores,stops=first_region(ROOT,body,caller)
    if backs:raise ValueError('SC decision backward')
    if not stops or any(k!=1 or (pc,dst) not in EDGES[1:3] for pc,k,_,dst in stops):
        raise ValueError('SC decision boundary')
    loads=[];writes=[]
    protected=[ring_object(d,e)[:2],credit_object(d,e),*layout(d,e),*event_plan(d,e)[3],final_plan(d,e)[1]]
    for pc,w in sorted(rows.items()):
        k=category(w);op=w>>26;ra=(w>>16)&31
        if k not in ('load','store'):continue
        n=({32:4,34:1,40:2} if k=='load' else {36:4,38:1,44:2}).get(op)
        if not n or ra not in (2,13):raise ValueError('SC decision memory form')
        a=(EXPECTED_GPRS[ra]+((w&0xffff)^0x8000)-0x8000)&0xffffffff
        obj=object_at(d,e,a,n)
        if k=='store' and any(obj[0]<b+m and b<obj[0]+obj[1] for b,m in protected):
            raise ValueError('SC decision object overlap')
        (loads if k=='load' else writes).append((pc,a,n,obj))
    if len(writes)!=stores:raise ValueError('SC decision store coverage')
    return rows,loads,writes,stops

def render(p):
    fields,ws=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    words=','.join('undercover::wii::IpcDispatchWord{'+fmt((fields[0],fields[0]+4*i,w))+'}' for i,w in enumerate(ws))
    return ('#pragma once\n#include "wii_post_stm_sc_disable.h"\nnamespace post_stm_sc_disable_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(ws)}> words'+'{'+words+'};\n'
        'inline constexpr undercover::wii::PostStmScDisableExpectation expected{'+fmt(fields)+',words};\n}\n')

def audit(root,p):
    fields,ws=p
    expected={fields[0]+4*i:(fields[0],w) for i,w in enumerate(ws)}
    sources=[x.read_text() for x in sorted(root.glob('output_*.cpp'))]
    audit_native(sources,(root/'main_output.cpp').read_text(),expected)
    for pc,(_,w) in expected.items():
        hook=f'    v1270_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
        if sum(s.count(hook) for s in sources)!=1:raise ValueError('SC disable hook')
    print(f'POST_STM_SC_DISABLE_TRANSLATION verified=1 labels={len(ws)} existing_hooks={len(ws)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--out',type=Path);m.add_argument('--audit',type=Path);m.add_argument('--decision',action='store_true');q=a.parse_args()
    safe={'size','disable extent','disable opcode','disable MSR count','disable identity','SC first decision',
          'SC decision backward','SC decision boundary','SC decision memory form','SC decision object overlap','SC decision store coverage',
          'SC disable hook','STM object identity','STM data request','STM object range','native IPC duplicate root',
          'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        fields,words=leaf_plan(d,e)
        if q.audit:audit(q.audit,(fields,words));return 0
        if q.out:
            with (q.out/'private_post_stm_sc_disable.h').open('x') as out:out.write(render((fields,words)))
        if q.decision:
            rows,loads,writes,stops=decision(d,e)
            print(f'POST_STM_SC_DECISION_GEOMETRY verified=1 labels={len(rows)} loads={len(loads)} stores={len(writes)} calls={len(stops)} original_execution=0')
            return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_DISABLE_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_DISABLE_GEOMETRY verified=1 leaf_labels={len(words)} msr_reads=1 msr_writes=1 caller=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
