#!/usr/bin/env python3
"""Private full formatter dependency fixture. Public logs contain counts only."""
import argparse,struct
from pathlib import Path
from private_plan_cache import memoized_plan,plan_cache_scope
from prepare_post_stm_sc_report_formatter_fixture import plan as prefix_plan,scope as prefix_scope
from prepare_post_stm_sc_report_formatter_path import plan as path_plan
from prepare_post_stm_sc_formatter_leaf_path import run
from prepare_post_stm_sc_report_dependency_abi import plan as leaf_abi
from prepare_post_stm_sc_report_dependency_path import execute
from prepare_post_stm_sc_version import plan as version_plan
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from make_v624_ipc_geometry import exact_words
from audit_handler_suffix_v728 import target

def merge(old,formatter,root,caller,ws):
    if len(ws)!=12 or formatter==root or old.get(root)!=(ws[0],GUARD):
        raise ValueError('formatter leaf predecessor')
    body=old.get(formatter,())
    off=caller-formatter
    if off<4 or off%4 or off//4>=len(body) or body[off//4]!=GUARD or direct_bl(body[off//4-1],caller-4)!=root:
        raise ValueError('formatter leaf guarded caller')
    return {**old,root:tuple(ws)}

def read_source(read,readonly,stack,sp):
    pc,(kind,at),width=read
    if width not in (1,2,4) or at%width:raise ValueError('formatter leaf read alignment')
    if kind=='stack':
        if not sp<=at<at+width<=0:raise ValueError('formatter leaf read extent')
        cells=[stack.get(at+i) for i in range(width)]
        if any(c is None or c[0]!='byte' for c in cells):raise ValueError('formatter leaf read bytes')
        return pc,True,at-sp,width,bytes(c[1] for c in cells)
    if kind!='const' or not 0x80000000<=at<at+width<=0x81800000:raise ValueError('formatter leaf read extent')
    data=[blob[at-base:at-base+width] for base,blob in readonly if base<=at<at+width<=base+len(blob)]
    if len(data)!=1:raise ValueError('formatter leaf read bytes')
    return pc,False,at,width,data[0]

@memoized_plan
def plan(d,e):
    prior=prefix_plan(d,e);old=prior[2]
    path,frame,accesses,saved,root,gp,mem,ws=path_plan(d,e)
    formatter=path[0];caller=path[-1]+4;body=exact_words(d,e,root,12)
    _,_,ranges,_=version_plan(d,e)
    _,args,obj,sites,_,blob,fields,leaf=leaf_abi(d,e)
    final=execute(fields[0],leaf,(args[0][1],args[1][1]),obj,sites,blob)[4]
    readonly=tuple(ranges)+((obj[0],final),)
    active,reads,value,reach,returns=run(root,body,gp,readonly,mem)
    if len(active)!=8 or len(set(active))!=8 or len(reach)!=12 or len(returns)!=3 or len(reads)!=1 or value[0]!='const':
        raise ValueError('formatter leaf active identity')
    if gp[1]!=('stack',-160-frame):raise ValueError('formatter leaf stack identity')
    source=read_source(reads[0],readonly,mem,gp[1][1])
    blocks=merge(old,formatter,root,caller,body)
    return prior,old,blocks,(root,caller,GUARD),body,active,source,value[1]

def render(p):
    _,_,_,fields,ws,active,source,value=p
    pc,stack,at,n,data=source
    f=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    back=sum(1 for pc in active if (w:=ws[(pc-fields[0])//4])>>26 in (16,18) and not w&3 and fields[0]<=target(pc,w)<=pc)
    wr=','.join('undercover::wii::IpcDispatchWord{'+f((fields[0],fields[0]+4*i,w))+'}' for i,w in enumerate(ws))
    return ('#pragma once\n#include "wii_post_stm_sc_leaf_shadow.h"\nnamespace post_stm_sc_formatter_leaf_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(ws)}> words'+'{'+wr+'};\n'
        f'inline constexpr std::array<uint32_t,{len(active)}> active'+'{'+f(active)+'};\n'
        'inline constexpr std::array<undercover::wii::ScLeafAccess,1> accesses{{{'+f((pc,0,n))+',false}}};\n'
        f'inline constexpr unsigned backward_polls={back}u;\n'
        f'inline constexpr bool stack_relative={str(stack).lower()};\n'
        'inline constexpr uint32_t address='+f((at,))+';\n'
        f'inline constexpr std::array<uint8_t,{n}> bytes'+'{'+','.join(str(v)+'u' for v in data)+'};\n'
        'inline constexpr undercover::wii::ScLeafExpectation expected{'+f(fields)+',words,accesses,0,0,0,active,true,'+f((value,))+'};\n}\n')

def extend(directory,p):
    _,old,blocks,*_=p
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()) or set(blocks)!=set(old):raise ValueError('formatter leaf predecessor')
    expanded={**live,**blocks};check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=59)
    with (directory/'private_post_stm_sc_formatter_leaf.h').open('x') as out:out.write(render(p))
    image.write_bytes(new);csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print('POST_STM_SC_FORMATTER_LEAF_FIXTURE verified=1 labels=12 active=8 guarded_caller=1 new_roots=0')

def scope(d,e,sizes,p):
    prior,old,blocks,fields,*_=p;root=fields[0]
    if set(blocks)!=set(old) or sizes.get(root)!=4*len(blocks[root]):raise ValueError('formatter leaf extent')
    spans=dict(prefix_scope(d,e,{**sizes,root:4*len(old[root])},prior))
    return check_spans({**spans,root:sizes[root]})

def install(directory,p):
    _,_,_,fields,ws,*_=p;root=fields[0]
    files=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in files}
    expected={root+4*i:(root,w) for i,w in enumerate(ws)}
    audit_native(sources.values(),(directory/'main_output.cpp').read_text(),expected)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('formatter leaf hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_formatter_leaf_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('formatter leaf hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid post_stm_sc_formatter_leaf_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('formatter leaf coverage')
    for file,s in changed.items():file.write_text(s)
    print('POST_STM_SC_FORMATTER_LEAF_TRANSLATION verified=1 labels=12')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','formatter leaf predecessor','formatter leaf guarded caller','formatter leaf active identity','formatter leaf stack identity','formatter leaf read alignment','formatter leaf read extent','formatter leaf read bytes','formatter leaf extent','formatter leaf hook','formatter leaf coverage'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        with plan_cache_scope():
            p=plan(d,e)
            if q.fixture:extend(q.fixture,p);return 0
            if q.install:install(q.install,p);return 0
            if q.analyzer:
                if not q.symbols:raise ValueError('formatter leaf extent')
                q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
                print('POST_STM_SC_FORMATTER_LEAF_ANALYZER verified=1 expanded_root=1 new_roots=0');return 0
            if not render(p):raise ValueError('formatter leaf extent')
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_FORMATTER_LEAF_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_FORMATTER_LEAF_PREP verified=1 labels=12 active=8 reads=1 read_kind={"stack" if p[6][1] else "data"} read_width={p[6][3]} guarded_caller=1 return_proven=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
