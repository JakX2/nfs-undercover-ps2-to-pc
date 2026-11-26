#!/usr/bin/env python3
"""Privately extend the SC native owner through version registration and report entry."""
import argparse
import re
import struct
from pathlib import Path
from prepare_post_stm_sc_version import plan as version_plan,ROOT,VERSION,REPORT
from prepare_post_stm_sc_decision import plan as decision_plan,scope as decision_scope
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit,ensure_resume
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function

def merge(old,rows,body,fields):
    start,version,report,report_word,_,_=fields
    prefix=old.get(ROOT)
    if not prefix or prefix[-1]!=GUARD or ROOT+4*(len(prefix)-1)!=start or version in old or report in old:
        raise ValueError('SC version fixture predecessor')
    if set(rows)!={start,start+4} or direct_bl(rows[start+4],start+4)!=version or not 3<=len(body)<=8:
        raise ValueError('SC version fixture extent')
    return {**old,ROOT:prefix[:-1]+(rows[start],rows[start+4],GUARD),version:tuple(body),report:(report_word,GUARD)}

def plan(d,e):
    prior=decision_plan(d,e)
    rows,body,ranges,fields=version_plan(d,e)
    old=prior[2];blocks=merge(old,rows,body,fields)
    return prior,old,blocks,rows,body,ranges,fields

def render(p):
    _,_,_,rows,body,ranges,fields=p
    start,version,report,report_word,ptr,fmt=fields
    f=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    words=[(ROOT,pc,w) for pc,w in sorted(rows.items())]+[(version,version+4*i,w) for i,w in enumerate(body)]
    data=[(a+i,v) for a,blob in ranges for i,v in enumerate(blob)]
    wr=','.join('undercover::wii::IpcDispatchWord{'+f(row)+'}' for row in words)
    br=','.join('undercover::wii::ScVersionByte{'+f((a,))+','+str(v)+'u}' for a,v in sorted(data))
    return ('#pragma once\n#include "wii_post_stm_sc_version.h"\nnamespace post_stm_sc_version_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+wr+'};\n'
        f'inline constexpr std::array<undercover::wii::ScVersionByte,{len(data)}> data'+'{'+br+'};\n'
        'inline constexpr undercover::wii::ScVersionExpectation expected{'+f((ROOT,start,version,report,report_word,ranges[0][0],ptr,fmt))+',words,data};\n}\n')

def extend(directory,p):
    _,old,blocks,rows,body,_,fields=p
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()) or (set(blocks)-set(old))&set(live):
        raise ValueError('SC version fixture predecessor')
    expanded={**live,**blocks}
    check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=55)
    with (directory/'private_post_stm_sc_version.h').open('x') as out:out.write(render(p))
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print(f'POST_STM_SC_VERSION_FIXTURE verified=1 caller_labels={len(rows)} thunk_labels={len(body)} new_roots=2 guarded_report=1')

def scope(d,e,sizes,p):
    prior,old,blocks,*_=p
    added=set(blocks)-set(old)
    if len(added)!=2 or any(sizes.get(a)!=4*len(blocks[a]) for a in (*added,ROOT)):
        raise ValueError('SC version fixture extent')
    before={a:n for a,n in sizes.items() if a not in added};before[ROOT]=4*len(old[ROOT])
    spans=dict(decision_scope(d,e,before,prior))
    return check_spans({**spans,**{a:sizes[a] for a in (*added,ROOT)}})

def verify_tail(source,site,report):
    hits=list(re.finditer(r'(?mi)^loc_'+f'{site:X}'+r': ;\n(.*?)(?=^loc_[0-9a-f]+: ;|\Z)',source,re.S|re.M))
    if len(hits)!=1 or sum(line.strip()==f'ctx.pc = 0x{report:X}; return;' for line in hits[0][1].splitlines())!=1:
        raise ValueError('SC version native tail')

def install(directory,p):
    _,_,_,rows,body,_,fields=p
    start,version,report,report_word,_,_=fields
    paths=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    main=directory/'main_output.cpp';text=main.read_text()
    expected={pc:(ROOT,w) for pc,w in rows.items()}
    expected.update({version+4*i:(version,w) for i,w in enumerate(body)})
    audit_native(sources.values(),text,{**expected,report:(report,report_word)})
    owners=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{ROOT:X}'+r'\(CPUContext& ctx\) \{',s)]
    thunks=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{version:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(owners)!=1 or len(thunks)!=1:raise ValueError('SC version owner')
    owner=exact_function(owners[0],ROOT);thunk=exact_function(thunks[0],version)
    verify_direct(owner,start+4,version);verify_tail(thunk,version+4*(len(body)-1),report)
    out,added=ensure_resume(text,owner,ROOT,start)
    done=set();changed={}
    for path,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('SC version hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_version_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('SC version hook')
            changed[path]=s.replace(anchor,anchor+'\nvoid post_stm_sc_version_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('SC version coverage')
    for path,s in changed.items():path.write_text(s)
    if added:main.write_text(out)
    print(f'POST_STM_SC_VERSION_TRANSLATION verified=1 original_labels={len(done)} direct_call=1 tail_dispatch=1 outer_resume=1 added={int(added)}')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','SC version fixture predecessor','SC version fixture extent','SC version native tail','SC version owner','SC version hook',
          'SC version coverage','fixture geometry','fixture range','fixture overlap','completion roundtrip','completion hook label',
          'completion local resume','completion root dispatch','completion outer resume','native IPC duplicate root',
          'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper direct native call',
          'helper native return edge','helper call label'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.fixture:extend(q.fixture,p);return 0
        if q.install:install(q.install,p);return 0
        if q.analyzer:
            if not q.symbols:raise ValueError('SC version fixture extent')
            q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
            print('POST_STM_SC_VERSION_ANALYZER verified=1 expanded_root=1 new_roots=2');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_VERSION_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('POST_STM_SC_VERSION_PREP verified=1 guarded_report=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
