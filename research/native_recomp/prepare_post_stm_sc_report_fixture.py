#!/usr/bin/env python3
"""Private native CR6-clear report path to the exact next original call."""
import argparse
import re
import struct
from pathlib import Path
from prepare_post_stm_sc_report import report_trace,REPORT
from prepare_post_stm_sc_report_abi import model
from prepare_post_stm_sc_version_fixture import plan as version_plan,scope as version_scope
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words

def merge(old,rows,path,dst,target_word):
    if old.get(REPORT)!=(rows.get(REPORT),GUARD) or dst in old or not path or path[0]!=REPORT:
        raise ValueError('SC report fixture predecessor')
    site=path[-1]
    if set(path)-set(rows) or direct_bl(rows[site],site)!=dst or not REPORT<=site<REPORT+256:
        raise ValueError('SC report fixture extent')
    # Preserve the static branch geometry, but guard off-path FP spills
    # and every unadmitted continuation. No alternate success stub.
    prefix=tuple(rows[pc] if pc in path else GUARD for pc in range(REPORT,site+4,4))
    return {**old,REPORT:prefix+(GUARD,),dst:(target_word,GUARD)}

def plan(d,e):
    prior=version_plan(d,e)
    old=prior[2]
    n=parse_functions(e).get(REPORT,0)
    if not 16<=n<=4096 or n%4:raise ValueError('SC report extent')
    ws=exact_words(d,e,REPORT,n//4)
    rows,path,slots,fp,frame,dst=report_trace(REPORT,ws)
    if model(REPORT,ws)!=(22,14,8,128,dst) or fp or len(path)!=22:
        raise ValueError('SC report ABI identity')
    target_word=exact_words(d,e,dst,1)[0]
    blocks=merge(old,rows,path,dst,target_word)
    return prior,old,blocks,rows,path,(REPORT,dst,target_word,frame),len(slots)

def render(p):
    _,_,_,rows,path,fields,stores=p
    f=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+f((REPORT,pc,rows[pc]))+'}' for pc in path)
    return ('#pragma once\n#include "wii_post_stm_sc_report.h"\nnamespace post_stm_sc_report_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(path)}> path'+'{'+wr+'};\n'
        'inline constexpr undercover::wii::ScReportExpectation expected{'+f(fields)+',path,'+str(stores)+'u};\n}\n')

def extend(directory,p):
    _,old,blocks,_,path,fields,_=p
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()) or (set(blocks)-set(old))&set(live):
        raise ValueError('SC report fixture predecessor')
    expanded={**live,**blocks}
    check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=56)
    with (directory/'private_post_stm_sc_report.h').open('x') as out:out.write(render(p))
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print(f'POST_STM_SC_REPORT_FIXTURE verified=1 path_labels={len(path)} new_roots=1 guarded_helper=1')

def scope(d,e,sizes,p):
    prior,old,blocks,_,_,fields,_=p
    dst=fields[1]
    if set(blocks)-set(old)!={dst} or any(sizes.get(a)!=4*len(blocks[a]) for a in (REPORT,dst)):
        raise ValueError('SC report fixture extent')
    before={a:n for a,n in sizes.items() if a!=dst};before[REPORT]=4*len(old[REPORT])
    spans=dict(version_scope(d,e,before,prior))
    return check_spans({**spans,REPORT:sizes[REPORT],dst:sizes[dst]})

def install(directory,p):
    _,_,_,rows,path,fields,_=p
    _,dst,target_word,_=fields
    paths=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    main=directory/'main_output.cpp'
    expected={pc:(REPORT,rows[pc]) for pc in path}
    audit_native(sources.values(),main.read_text(),{**expected,dst:(dst,target_word)})
    owners=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{REPORT:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(owners)!=1:raise ValueError('SC report owner')
    verify_direct(exact_function(owners[0],REPORT),path[-1],dst)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('SC report hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_report_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('SC report hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid post_stm_sc_report_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('SC report coverage')
    for file,s in changed.items():file.write_text(s)
    print(f'POST_STM_SC_REPORT_TRANSLATION verified=1 path_labels={len(done)} direct_call=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','SC report fixture predecessor','SC report fixture extent','SC report extent','SC report ABI identity',
          'SC report owner','SC report hook','SC report coverage','fixture geometry','fixture range','fixture overlap','completion roundtrip',
          'completion hook label','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage',
          'native IPC dispatch','helper direct native call','helper native return edge','helper call label'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.fixture:extend(q.fixture,p);return 0
        if q.install:install(q.install,p);return 0
        if q.analyzer:
            if not q.symbols:raise ValueError('SC report fixture extent')
            q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
            print('POST_STM_SC_REPORT_ANALYZER verified=1 expanded_root=1 new_roots=1');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('POST_STM_SC_REPORT_PREP verified=1 guarded_helper=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
