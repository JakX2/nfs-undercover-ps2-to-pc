#!/usr/bin/env python3
"""Private SC cold-decision fixture, preserving the original native caller."""
import argparse
import re
import struct
from pathlib import Path
from prepare_post_stm_sc_join import ROOT,EDGES,GUARD,plan as entry_plan,blocks_for,scope as entry_scope,check_spans
from prepare_post_stm_sc_disable import decision,leaf_plan
from prepare_post_stm_sc_state import derive as state_plan
from prepare_v1337_open_completion import plan as completion,RESTORE,rebuild,hook_submit,ensure_resume
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function

def merge(old,rows,start,calls):
    # Keep one original SC owner; every hole and unadmitted continuation
    # is an explicit fail-closed guard, never a successful return stub.
    prefix=old.get(ROOT)
    if not prefix or prefix[-1]!=GUARD or ROOT+4*(len(prefix)-1)!=start:
        raise ValueError('SC decision predecessor')
    if not rows or min(rows)!=start or len(rows)!=8 or len(calls)!=2 or set(calls)-set(rows):
        raise ValueError('SC decision extent')
    end=max(rows)
    if end-start>64 or any(pc&3 or pc<start for pc in rows):
        raise ValueError('SC decision extent')
    for pc,dst in calls.items():
        if dst!=RESTORE or direct_bl(rows[pc],pc)!=dst or pc+4 in rows:
            raise ValueError('SC decision guard')
    tail=tuple(rows.get(pc,GUARD) for pc in range(start,end+4,4))+(GUARD,)
    return {**old,ROOT:prefix[:-1]+tail}

def plan(d,e):
    prior=entry_plan(d,e)
    (disable,start,word),_=leaf_plan(d,e)
    rows,loads,writes,stops=decision(d,e)
    kind,zero,seeded,objects,same,cells=state_plan(d,e)
    if (kind,zero,seeded,objects,same,cells)!=(2,1,0,2,1,1):
        raise ValueError('SC decision cold provenance')
    if rows.get(start)!=word or len(loads)!=1 or len(writes)!=2 or len(stops)!=2:
        raise ValueError('SC decision extent')
    calls={pc:dst for pc,k,_,dst in stops if k==1}
    if calls!=dict(EDGES[1:3]):raise ValueError('SC decision calls')
    for pc,w in rows.items():
        op=w>>26;xo=(w>>1)&1023
        if op not in (10,11,14,15,16,18,24,25,32,34,36,38,40,44) and not(op==31 and xo==444 and not w&1):
            raise ValueError('SC decision opcode')
    old=blocks_for(prior);blocks=merge(old,rows,start,calls)
    shared,*_=completion(d,e)
    return prior,old,blocks,(ROOT,start,RESTORE,shared[RESTORE][0],EDGES[2][0]),rows,loads[0],writes,calls

def render(p):
    _,_,_,fields,rows,load,writes,_=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    def cell(row):
        pc,a,n,obj=row
        return 'undercover::wii::ScDecisionCell{'+fmt((pc,a,n))+',undercover::wii::AllocatorRange{'+fmt(obj)+'}}'
    words=','.join('undercover::wii::IpcDispatchWord{'+fmt((ROOT,pc,w))+'}' for pc,w in sorted(rows.items()))
    return ('#pragma once\n#include "wii_post_stm_sc_decision.h"\nnamespace post_stm_sc_decision_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(rows)}> words'+'{'+words+'};\n'
        'inline constexpr std::array<undercover::wii::ScDecisionCell,2> stores{'+','.join(map(cell,writes))+'};\n'
        'inline constexpr undercover::wii::ScDecisionExpectation expected{'+fmt(fields)+','+cell(load)+',stores,words};\n}\n')

def extend(directory,p):
    _,old,blocks,fields,rows,_,_,calls=p
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()):raise ValueError('SC decision predecessor')
    expanded={**live,**blocks}
    check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=53)
    with (directory/'private_post_stm_sc_decision.h').open('x') as out:out.write(render(p))
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print(f'POST_STM_SC_DECISION_FIXTURE verified=1 original_labels={len(rows)} guarded_returns={len(calls)} root_count_unchanged=1')

def scope(d,e,sizes,p):
    prior,old,blocks,*_=p
    if sizes.get(ROOT)!=4*len(blocks[ROOT]):raise ValueError('SC decision extent')
    before={**sizes,ROOT:4*len(old[ROOT])}
    spans=dict(entry_scope(d,e,before,prior))
    return check_spans({**spans,ROOT:sizes[ROOT]})

def install(directory,p):
    _,_,_,fields,rows,_,_,calls=p
    paths=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    main=directory/'main_output.cpp';text=main.read_text()
    expected={pc:(ROOT,w) for pc,w in rows.items()}
    audit_native(sources.values(),text,expected)
    owners=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{ROOT:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(owners)!=1:raise ValueError('SC decision owner')
    owner=exact_function(owners[0],ROOT)
    for pc,dst in calls.items():verify_direct(owner,pc,dst)
    out,added=ensure_resume(text,owner,ROOT,fields[1])
    done=set();changed={}
    for path,s in sources.items():
        old=s
        for pc,w in rows.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('SC decision hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_decision_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('SC decision hook')
            changed[path]=s.replace(anchor,anchor+'\nvoid post_stm_sc_decision_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(rows):raise ValueError('SC decision coverage')
    for path,s in changed.items():path.write_text(s)
    if added:main.write_text(out)
    print(f'POST_STM_SC_DECISION_TRANSLATION verified=1 original_labels={len(done)} direct_edges={len(calls)} outer_resume=1 added={int(added)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','SC decision predecessor','SC decision extent','SC decision guard','SC decision cold provenance','SC decision calls',
          'SC decision opcode','SC decision owner','SC decision hook','SC decision coverage','fixture geometry','fixture range','fixture overlap',
          'completion roundtrip','completion hook label','completion local resume','completion root dispatch','completion outer resume',
          'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
          'helper direct native call','helper native return edge','helper call label'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.fixture:extend(q.fixture,p);return 0
        if q.install:install(q.install,p);return 0
        if q.analyzer:
            if not q.symbols:raise ValueError('SC decision extent')
            q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
            print('POST_STM_SC_DECISION_ANALYZER verified=1 expanded_root=1');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_DECISION_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('POST_STM_SC_DECISION_PREP verified=1 cold_bss=1 original_labels=8 store_objects=2 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
