#!/usr/bin/env python3
"""Private native report helper prefix, keeping both parent frames live."""
import argparse
import re
import struct
from pathlib import Path
from prepare_post_stm_sc_report_fixture import plan as report_plan,scope as report_scope
from prepare_post_stm_sc_report_helper_prefix import prefix
from prepare_post_stm_sc_report import report_trace,REPORT
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct,exact_function
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words

def merge(old,root,words,dst,word):
    if old.get(root)!=(words[0],GUARD) or dst in old or len(words)!=13 or direct_bl(words[-1],root+48)!=dst:
        raise ValueError('SC report helper fixture predecessor')
    return {**old,root:tuple(words)+(GUARD,),dst:(word,GUARD)}

def plan(d,e):
    prior=report_plan(d,e);old=prior[2];root=prior[5][1]
    sizes=parse_functions(e)
    if sizes.get(root)!=120:raise ValueError('SC report helper extent')
    ws=exact_words(d,e,root,30)
    n,frame,stores,loads,saved,dst=prefix(root,ws)
    if (n,frame,stores,loads,len(saved),sizes.get(dst))!=(13,32,5,0,3,132):
        raise ValueError('SC report helper ABI identity')
    report=exact_words(d,e,REPORT,sizes[REPORT]//4)
    _,path,slots,_,parent_frame,_=report_trace(REPORT,report)
    if any(at< -parent_frame+8 and -parent_frame+4<at+width for at,width in slots):
        raise ValueError('SC report parent linkage occupied')
    entry_lr=path[-1]+4;word=exact_words(d,e,dst,1)[0]
    blocks=merge(old,root,ws[:n],dst,word)
    return prior,old,blocks,(root,entry_lr,dst,word,frame),tuple(ws[:n]),tuple(sorted({**saved,4:32}.items()))

def render(p):
    _,_,_,fields,words,slots=p
    f=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+f((fields[0],fields[0]+4*i,w))+'}' for i,w in enumerate(words))
    sr=','.join('undercover::wii::StmFinalSlot{'+str(at)+','+str(reg)+'u}' for at,reg in slots)
    return ('#pragma once\n#include "wii_post_stm_sc_report_helper.h"\nnamespace post_stm_sc_report_helper_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+wr+'};\n'
        f'inline constexpr std::array<undercover::wii::StmFinalSlot,{len(slots)}> slots'+'{'+sr+'};\n'
        'inline constexpr undercover::wii::ScReportHelperExpectation expected{'+f(fields)+',words,slots};\n}\n')

def extend(directory,p):
    _,old,blocks,fields,words,_=p
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()) or (set(blocks)-set(old))&set(live):
        raise ValueError('SC report helper fixture predecessor')
    expanded={**live,**blocks}
    check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=57)
    with (directory/'private_post_stm_sc_report_helper.h').open('x') as out:out.write(render(p))
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print(f'POST_STM_SC_REPORT_HELPER_FIXTURE verified=1 labels={len(words)} new_roots=1 guarded_next=1')

def scope(d,e,sizes,p):
    prior,old,blocks,fields,*_=p;root,_,dst,*_=fields
    if set(blocks)-set(old)!={dst} or any(sizes.get(a)!=4*len(blocks[a]) for a in (root,dst)):
        raise ValueError('SC report helper extent')
    before={a:n for a,n in sizes.items() if a!=dst};before[root]=4*len(old[root])
    spans=dict(report_scope(d,e,before,prior))
    return check_spans({**spans,root:sizes[root],dst:sizes[dst]})

def install(directory,p):
    _,_,_,fields,words,_=p
    root,_,dst,target_word,_=fields
    paths=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    main=directory/'main_output.cpp'
    expected={root+4*i:(root,w) for i,w in enumerate(words)}
    audit_native(sources.values(),main.read_text(),{**expected,dst:(dst,target_word)})
    owners=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{root:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(owners)!=1:raise ValueError('SC report helper owner')
    verify_direct(exact_function(owners[0],root),root+4*(len(words)-1),dst)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('SC report helper hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_report_helper_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('SC report helper hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid post_stm_sc_report_helper_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('SC report helper coverage')
    for file,s in changed.items():file.write_text(s)
    print(f'POST_STM_SC_REPORT_HELPER_TRANSLATION verified=1 labels={len(done)} direct_call=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','SC report helper fixture predecessor','SC report helper extent','SC report helper ABI identity','SC report parent linkage occupied',
          'SC report helper owner','SC report helper hook','SC report helper coverage','fixture geometry','fixture range','fixture overlap','completion roundtrip',
          'completion hook label','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage',
          'native IPC dispatch','helper direct native call','helper native return edge','helper call label'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.fixture:extend(q.fixture,p);return 0
        if q.install:install(q.install,p);return 0
        if q.analyzer:
            if not q.symbols:raise ValueError('SC report helper extent')
            q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
            print('POST_STM_SC_REPORT_HELPER_ANALYZER verified=1 expanded_root=1 new_roots=1');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_HELPER_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('POST_STM_SC_REPORT_HELPER_PREP verified=1 guarded_next=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
