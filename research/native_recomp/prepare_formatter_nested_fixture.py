#!/usr/bin/env python3
"""Private finite nested fixture. The unresolved load is an observed stop."""
import argparse,struct
from pathlib import Path
from private_plan_cache import plan_cache_scope
from prepare_formatter_nested_contract import plan as nested_plan
from prepare_formatter_second_contract import plan as second_plan
from prepare_formatter_third_contract import plan as third_plan
from prepare_formatter_control_contract import plan as control_plan
from prepare_formatter_post_ctr_contract import plan as post_ctr_plan
from prepare_formatter_partial_native_contract import plan as partial_plan
from prepare_formatter_special_contract import plan as special_plan
from prepare_formatter_continuation_plan import plan as continuation_plan
from prepare_formatter_continuation_fixture import scope as continuation_scope
from prepare_post_stm_sc_join import check_spans
from prepare_v1337_open_completion import rebuild,hook_submit
from prepare_v419_full_start import MAX_DOL,words_at
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from formatter_local_ctr_native import verify_ctr_body,ensure_ctr_resume,analyzer_local_edge,trace_ctr_destination
from prepare_v680_si_helper import exact_function

def plan(d,e,*,second=False,third=False,control=False):
    if sum((second,third,control))>1:raise ValueError('nested fixture mode')
    prior=continuation_plan(d,e,details=True)
    first=nested_plan(d,e,previous=prior[1])
    if not (second or third or control):return prior,first
    two=second_plan(d,e,previous=prior[1],first=first)
    if second:return prior,two
    three=third_plan(d,e,previous=prior[1],second=two)
    return prior,control_plan(d,e,previous=prior[1],third=three) if control else three

def render(contract,*,stack_boundary=False,instruction_boundary=False,special_boundary=False):
    if special_boundary and not instruction_boundary:raise ValueError('nested fixture instruction boundary')
    _,fields,rows,access,slots,known=contract
    root,caller,target,word,frame,addr,width,*control=fields
    if control and (len(control)!=3 or addr or width or word!=0x4e800420):raise ValueError('nested fixture control contract')
    if stack_boundary and (control or width!=4 or addr%4 or not -44<=addr<=-4):raise ValueError('nested fixture stack boundary')
    if instruction_boundary and (stack_boundary or control or addr or width):raise ValueError('nested fixture instruction boundary')
    namespace='formatter_special_private' if special_boundary else 'formatter_partial_private' if instruction_boundary else 'formatter_post_ctr_private' if stack_boundary else 'formatter_nested_private'
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+fmt((root,pc,w))+'}' for pc,w in rows)
    values={pc:int.from_bytes(data,'big') for pc,_,data in known}
    if len(values)!=len(known) or any(sum(site[0]==pc and not site[3] and not site[4] and site[2]==at and site[1]==len(data) for site in access)!=1 for pc,at,data in known):
        raise ValueError('nested fixture data contract')
    if any(not stack and not write and pc not in values for pc,_,_,stack,write in access):
        raise ValueError('nested fixture data contract')
    ar=','.join('undercover::wii::ScFormatterAccess{'+fmt((pc,n))+','+str(at)+','+str(stack).lower()+','+str(write).lower()+
                (','+fmt((values[pc],)) if pc in values else '')+'}' for pc,n,at,stack,write in access)
    sr=','.join('undercover::wii::StmFinalSlot{'+str(at)+','+str(reg)+'u}' for at,reg in slots)
    boundary='{0u,0u,false,0,true}' if instruction_boundary else '{0u,4u,true,'+str(addr)+'}' if stack_boundary else '{'+fmt((addr,width))+'}'
    return ('#pragma once\n#include "wii_post_stm_sc_formatter.h"\nnamespace '+namespace+' {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(rows)}> path'+'{'+wr+'};\n'
        f'inline constexpr std::array<undercover::wii::ScFormatterAccess,{len(access)}> accesses'+'{'+ar+'};\n'
        f'inline constexpr std::array<undercover::wii::StmFinalSlot,{len(slots)}> slots'+'{'+sr+'};\n'
        'inline constexpr undercover::wii::ScFormatterExpectation expected{'+fmt((root,caller,target,word,frame))+',path,accesses,slots,'+boundary+(',{'+fmt(control)+'}' if control else '')+'};\n}\n')

def expand(old,blocks,live,root):
    if set(blocks)!=set(old) or root not in old or any(live.get(a)!=ws for a,ws in old.items()):
        raise ValueError('nested fixture predecessor')
    if any(blocks[a]!=ws for a,ws in old.items() if a!=root) or len(blocks[root])<=len(old[root]):
        raise ValueError('nested fixture expansion')
    result={**live,**blocks}
    check_spans({a:4*len(ws) for a,ws in result.items()})
    return result

def extend(directory,p,*,post=None,partial=None,special=None):
    if special is not None and partial is None:raise ValueError('nested fixture mode')
    if partial is not None and post is None:raise ValueError('nested fixture mode')
    prior,contract=p;old=prior[1][0];final=special or partial or post or contract;blocks,fields,*_=final;root=fields[0]
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    expanded=expand(old,blocks,live,root)
    new=rebuild(raw,expanded,max_roots=60)
    header=render(contract)
    if post is not None:header+=render(post,stack_boundary=True)
    if partial is not None:header+=render(partial,instruction_boundary=True)
    if special is not None:header+=render(special,instruction_boundary=True,special_boundary=True)
    with (directory/'private_formatter_nested.h').open('x') as out:out.write(header)
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    kind='guarded_instruction' if partial is not None else 'guarded_stack' if post is not None else 'guarded_control' if len(fields)==10 else 'guarded_load'
    print(f'FORMATTER_NESTED_FIXTURE verified=1 labels={len(final[2])} {kind}=1 new_roots=0')

def scope(d,e,sizes,p):
    prior,contract=p;old=prior[1][0];blocks,fields,*_=contract;root=fields[0]
    if set(blocks)!=set(old) or sizes.get(root)!=4*len(blocks[root]):
        raise ValueError('nested fixture extent')
    before={**sizes,root:4*len(old[root])}
    return check_spans({**dict(continuation_scope(d,e,before,prior)),root:sizes[root]})

def install(directory,p,*,arrival=False,post=None,partial=None,special=None):
    if special is not None and partial is None:raise ValueError('nested fixture mode')
    if partial is not None and (post is None or not arrival):raise ValueError('nested fixture mode')
    _,contract=p
    _,fields,rows,*_=(special or partial or post or contract);root,_,target,word,*_=fields
    control_fields=contract[1]
    files=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in files}
    expected={pc:(root,w) for pc,w in rows}
    if target in expected:raise ValueError('nested fixture load boundary')
    expected[target]=(root,word)
    main=directory/'main_output.cpp';main_text=main.read_text()
    if arrival:
        if len(control_fields)!=10:raise ValueError('nested fixture arrival mode')
        dst,dword,_=control_fields[7:]
        if post is None:
            if dst in expected:raise ValueError('nested fixture arrival mode')
            expected[dst]=(root,dword)
        elif expected.get(dst)!=(root,dword):raise ValueError('nested fixture arrival mode')
    audit_native(sources.values(),main_text,expected)
    if len(control_fields)==10:
        owners=[]
        for source in sources.values():
            try:owners.append(exact_function(source,root))
            except ValueError:pass
        if len(owners)!=1:raise ValueError('nested fixture control owner')
        site=control_fields[2]
        verify_ctr_body(owners[0],site)
        if arrival:main_text,_=ensure_ctr_resume(main_text,owners[0],root,site,dst)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('nested fixture native hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','formatter_nested_before'))
            if arrival and pc==dst:s=trace_ctr_destination(s,pc,w)
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('nested fixture native hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid formatter_nested_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('nested fixture coverage')
    for file,s in changed.items():file.write_text(s)
    if arrival:main.write_text(main_text)
    kind='partial_hook' if partial is not None else 'post_ctr_hook' if post is not None else 'arrival_hook' if arrival else 'pre_control_hook' if len(fields)==10 else 'pre_load_hook'
    print(f'FORMATTER_NESTED_TRANSLATION verified=1 labels={len(rows)} {kind}=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);modes=a.add_mutually_exclusive_group();modes.add_argument('--second',action='store_true');modes.add_argument('--third',action='store_true');modes.add_argument('--control',action='store_true');modes.add_argument('--arrival',action='store_true');modes.add_argument('--post-ctr',action='store_true');modes.add_argument('--partial',action='store_true');modes.add_argument('--special',action='store_true');q=a.parse_args()
    safe={'size','nested fixture instruction boundary','nested fixture stack boundary','CTR analyzer geometry','CTR analyzer anchor','CTR destination trace','CTR native destination','completion local resume','completion outer resume','completion root dispatch','nested fixture arrival mode','CTR native body','nested fixture control owner','nested fixture control contract','nested fixture mode','nested fixture data contract','nested fixture predecessor','nested fixture expansion','nested fixture extent','nested fixture load boundary','nested fixture native hook','nested fixture coverage'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        with plan_cache_scope():
            p=plan(d,e,second=q.second,third=q.third,control=q.control or q.arrival or q.post_ctr or q.partial or q.special)
            post=post_ctr_plan(d,e,previous=p[0][1],control=p[1]) if q.post_ctr or q.partial or q.special else None
            partial=partial_plan(d,e,previous=p[0][1],control=p[1],post=post) if q.partial or q.special else None
            special=None
            if q.special:
                special,info=special_plan(d,e,previous=p[0][1],control=p[1],post=post,partial=partial)
                if info[:2]!=('link',1):raise ValueError('nested fixture special provenance')
            if q.fixture:extend(q.fixture,p,post=post,partial=partial,special=special);return 0
            if q.install:install(q.install,p,arrival=q.arrival or q.post_ctr or q.partial or q.special,post=post,partial=partial,special=special);return 0
            if q.analyzer:
                if not q.symbols:raise ValueError('nested fixture extent')
                source=analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),(p[0],special or partial or post) if post is not None else p))
                if q.arrival or q.post_ctr or q.partial or q.special:
                    fields=p[1][1];source=analyzer_local_edge(source,fields[0],fields[2],fields[7])
                q.analyzer.write_text(source)
                print('FORMATTER_NESTED_ANALYZER verified=1 expanded_root=1 new_roots=0');return 0
            if not render(p[1]) or (post is not None and not render(post,stack_boundary=True)) or (partial is not None and not render(partial,instruction_boundary=True)) or (special is not None and not render(special,instruction_boundary=True,special_boundary=True)):raise ValueError('nested fixture extent')
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_NESTED_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    kind='pre_control_hook' if q.control else 'pre_load_hook'
    print(f'FORMATTER_NESTED_PREP verified=1 labels={len(p[1][2])} {kind}=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
