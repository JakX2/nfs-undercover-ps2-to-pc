#!/usr/bin/env python3
"""Private full diagnostic dependency leaf with authenticated object data."""
import argparse,re,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_fixture import plan as helper_plan,scope as helper_scope
from prepare_post_stm_sc_report_dependency_abi import plan as abi_plan
from prepare_post_stm_sc_report_dependency import census
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit
from prepare_v419_full_start import MAX_DOL,words_at
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native

def merge(old,helper,fields,ws):
    root,caller,caller_word=fields
    if len(ws)!=33 or old.get(root)!=(ws[0],GUARD) or helper not in old or old[helper][-1]!=GUARD or helper+4*(len(old[helper])-1)!=caller:
        raise ValueError('SC report dependency predecessor')
    return {**old,root:tuple(ws)}

def plan(d,e):
    prior=helper_plan(d,e);old=prior[2];helper=prior[3][0]
    _,args,obj,sites,kind,blob,fields,ws=abi_plan(d,e)
    if args[0][0]!='const' or args[1][0]!='const' or fields[0]!=prior[3][2]:
        raise ValueError('SC report dependency identity')
    blocks=merge(old,helper,fields,ws)
    return prior,old,blocks,fields,ws,obj,sites,kind,blob,(args[0][1],args[1][1])

def render(p):
    _,_,_,fields,ws,obj,sites,kind,blob,args=p
    f=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+f((fields[0],fields[0]+4*i,w))+'}' for i,w in enumerate(ws))
    ar=','.join('undercover::wii::ScLeafAccess{'+f((pc,a-obj[0],n))+','+str(wr).lower()+'}' for pc,a,n,wr in sites)
    br=','.join(str(v)+'u' for v in blob)
    return ('#pragma once\n#include "wii_post_stm_sc_leaf_shadow.h"\nnamespace post_stm_sc_report_dependency_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(ws)}> words'+'{'+wr+'};\n'
        f'inline constexpr std::array<undercover::wii::ScLeafAccess,{len(sites)}> accesses'+'{'+ar+'};\n'
        f'inline constexpr std::array<uint8_t,{len(blob)}> initial'+'{'+br+'};\n'
        'inline constexpr undercover::wii::AllocatorRange object{'+f(obj)+'};\n'
        'inline constexpr uint32_t argument='+f((args[0],))+';\n'
        'inline constexpr uint32_t selector='+f((args[1],))+';\n'
        'inline constexpr unsigned initial_kind='+str(kind)+'u;\n'
        'inline constexpr undercover::wii::ScLeafExpectation expected{'+f(fields)+',words,accesses};\n}\n')

def extend(directory,p):
    _,old,blocks,fields,ws,*_=p
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()) or set(blocks)!=set(old):
        raise ValueError('SC report dependency predecessor')
    expanded={**live,**blocks}
    check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=57)
    with (directory/'private_post_stm_sc_report_dependency.h').open('x') as out:out.write(render(p))
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print(f'POST_STM_SC_REPORT_DEPENDENCY_FIXTURE verified=1 labels={len(ws)} new_roots=0 guarded_caller=1')

def scope(d,e,sizes,p):
    prior,old,blocks,fields,*_=p;root=fields[0];helper=prior[3][0]
    if set(blocks)!=set(old) or any(sizes.get(a)!=4*len(blocks[a]) for a in (root,helper)):
        raise ValueError('SC report dependency extent')
    before={**sizes,root:4*len(old[root]),helper:4*len(old[helper])}
    spans=dict(helper_scope(d,e,before,prior))
    return check_spans({**spans,root:sizes[root],helper:sizes[helper]})

def install(directory,p):
    prior,_,_,fields,ws,*_=p;root,caller,caller_word=fields;helper=prior[3][0]
    paths=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    main=directory/'main_output.cpp'
    expected={root+4*i:(root,w) for i,w in enumerate(ws)}
    audit_native(sources.values(),main.read_text(),expected)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('SC report dependency hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_report_dependency_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('SC report dependency hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid post_stm_sc_report_dependency_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('SC report dependency coverage')
    for file,s in changed.items():file.write_text(s)
    print(f'POST_STM_SC_REPORT_DEPENDENCY_TRANSLATION verified=1 labels={len(done)} returns=2')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','SC report dependency predecessor','SC report dependency identity','SC report dependency extent','SC report dependency hook',
          'SC report dependency coverage','fixture geometry','fixture range','fixture overlap','completion roundtrip','completion hook label',
          'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.fixture:extend(q.fixture,p);return 0
        if q.install:install(q.install,p);return 0
        if q.analyzer:
            if not q.symbols:raise ValueError('SC report dependency extent')
            q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
            print('POST_STM_SC_REPORT_DEPENDENCY_ANALYZER verified=1 expanded_root=1 new_roots=0');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_DEPENDENCY_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('POST_STM_SC_REPORT_DEPENDENCY_PREP verified=1 guarded_caller=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
