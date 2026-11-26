#!/usr/bin/env python3
"""Private native helper continuation to the authenticated formatter entry."""
import argparse,re,struct
from pathlib import Path
from prepare_post_stm_sc_report_dependency_fixture import plan as leaf_plan,scope as leaf_scope
from prepare_post_stm_sc_report_helper_resume import plan as resume_plan
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit,ensure_resume
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct

def merge(old,root,ws,path,site,dst,word):
    start=root+52
    if len(path)!=8 or path[0]!=start or path[-1]!=site or dst in old or old.get(root)!=tuple(ws[:13])+(GUARD,):
        raise ValueError('SC report resume predecessor')
    if len(set(path))!=8 or any(pc<start or pc>site or pc&3 for pc in path) or direct_bl(ws[(site-root)//4],site)!=dst:
        raise ValueError('SC report resume path')
    body=tuple(ws[:13])+tuple(ws[(pc-root)//4] if pc in path else GUARD for pc in range(start,site+4,4))+(GUARD,)
    return {**old,root:body,dst:(word,GUARD)}

def plan(d,e):
    prior=leaf_plan(d,e);old=prior[2]
    root,ws,path,site,dst,args,word,callback,callback_word=resume_plan(d,e,details=True)
    if callback!=args[0][1] or args[3][0]!='stack' or not -128<=args[3][1]<=-12:
        raise ValueError('SC report resume arguments')
    blocks=merge(old,root,ws,path,site,dst,word)
    return prior,old,blocks,(root,path[0],ws[13],dst,word),tuple((pc,ws[(pc-root)//4]) for pc in path),args,callback_word

def render(p):
    _,_,_,fields,rows,args,callback_word=p
    root,start,caller_word,dst,word=fields
    f=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+f((root,pc,w))+'}' for pc,w in rows)
    return ('#pragma once\n#include "wii_post_stm_sc_leaf_shadow.h"\nnamespace post_stm_sc_report_resume_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(rows)}> words'+'{'+wr+'};\n'
        'inline constexpr std::array<uint32_t,3> args{'+f([v[1] for v in args[:3]])+'};\n'
        'inline constexpr int32_t va_offset='+str(args[3][1])+';\n'
        'inline constexpr uint32_t callback_word='+f((callback_word,))+';\n'
        'inline constexpr undercover::wii::ScLeafExpectation expected{'+f((root,start,caller_word))+',words,{},'+f((start,dst,word))+'};\n}\n')

def extend(directory,p):
    _,old,blocks,fields,rows,*_=p
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()) or (set(blocks)-set(old))&set(live):raise ValueError('SC report resume predecessor')
    expanded={**live,**blocks};check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=58)
    with (directory/'private_post_stm_sc_report_resume.h').open('x') as out:out.write(render(p))
    image.write_bytes(new);csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print(f'POST_STM_SC_REPORT_RESUME_FIXTURE verified=1 labels={len(rows)} new_roots=1 guarded_formatter=1')

def scope(d,e,sizes,p):
    prior,old,blocks,fields,*_=p;root,_,_,dst,_=fields
    if set(blocks)-set(old)!={dst} or any(sizes.get(a)!=4*len(blocks[a]) for a in (root,dst)):raise ValueError('SC report resume extent')
    before={a:n for a,n in sizes.items() if a!=dst};before[root]=4*len(old[root])
    spans=dict(leaf_scope(d,e,before,prior))
    return check_spans({**spans,root:sizes[root],dst:sizes[dst]})

def trace_resume_entry(source,pc,w):
    # A resumed interior label is not a function root: the generated
    # root trace is conditional on ctx.pc == owner. Install a distinct
    # authenticated trace before the original instruction tick.
    label=r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n'
    pat=re.compile(label+r'    \+\+ctx\.inst_count;\n    post_stm_sc_report_resume_before\(ctx,0x'+f'{pc:08x}u,0x{w:08x}u'+r'\);')
    hits=list(pat.finditer(source))
    if len(hits)!=1:raise ValueError('SC report resume entry trace')
    hit=hits[0];i=hit.start()+len(re.match(label,source[hit.start():])[0])
    line=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx); // original report resume entry\n'
    if line in source:raise ValueError('SC report resume entry trace')
    return source[:i]+line+source[i:]

def install(directory,p):
    _,_,_,fields,rows,*_=p;root,start,_,dst,word=fields
    paths=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    main=directory/'main_output.cpp';main_text=main.read_text()
    expected={pc:(root,w) for pc,w in rows}
    audit_native(sources.values(),main_text,{**expected,dst:(dst,word)})
    owners=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{root:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(owners)!=1:raise ValueError('SC report resume owner')
    body=exact_function(owners[0],root);verify_direct(body,rows[-1][0],dst)
    main_text,_=ensure_resume(main_text,body,root,start)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('SC report resume hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_report_resume_before'))
            if pc==start:s=trace_resume_entry(s,pc,w)
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('SC report resume hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid post_stm_sc_report_resume_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('SC report resume coverage')
    for file,s in changed.items():file.write_text(s)
    main.write_text(main_text)
    print(f'POST_STM_SC_REPORT_RESUME_TRANSLATION verified=1 labels={len(done)} direct_call=1 outer_resume=1 entry_trace=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','SC report resume predecessor','SC report resume path','SC report resume arguments','SC report resume extent','SC report resume owner','SC report resume entry trace','SC report resume hook','SC report resume coverage','fixture geometry','fixture range','fixture overlap','completion roundtrip','completion hook label','completion local resume','completion root dispatch','completion outer resume','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge','helper call label'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.fixture:extend(q.fixture,p);return 0
        if q.install:install(q.install,p);return 0
        if q.analyzer:
            if not q.symbols:raise ValueError('SC report resume extent')
            q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
            print('POST_STM_SC_REPORT_RESUME_ANALYZER verified=1 expanded_root=1 new_roots=1');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_RESUME_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('POST_STM_SC_REPORT_RESUME_PREP verified=1 guarded_formatter=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
