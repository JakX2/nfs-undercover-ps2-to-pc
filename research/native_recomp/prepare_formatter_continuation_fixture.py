#!/usr/bin/env python3
"""Private in-process adapter for the verified finite continuation contract."""
import argparse,re,struct
from pathlib import Path
from private_plan_cache import plan_cache_scope
from prepare_formatter_continuation_plan import plan
from prepare_post_stm_sc_formatter_leaf_fixture import scope as leaf_scope,render as leaf_render
from prepare_post_stm_sc_join import check_spans
from prepare_v1337_open_completion import rebuild,hook_submit,ensure_resume
from prepare_v419_full_start import MAX_DOL,words_at
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct

def render(contract):
    _,root,start,dst,word,rows,mask,args=contract
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+fmt((root,pc,w))+'}' for pc,w in rows)
    # The symbolic reference SP is 160+704 bytes above the live SP.
    ar=','.join('undercover::wii::RegisterContinuationArgument{'+str(i)+'u,'+str(v+864 if k=='stack' else v)+','+str(k=='stack').lower()+'}' for i,k,v in args)
    return ('#pragma once\n#include "wii_register_continuation.h"\nnamespace formatter_continuation_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(rows)}> path'+'{'+wr+'};\n'
        f'inline constexpr std::array<undercover::wii::RegisterContinuationArgument,{len(args)}> args'+'{'+ar+'};\n'
        'inline constexpr undercover::wii::RegisterContinuationSpec expected{'+fmt((root,start,dst,word,mask))+',path,args};\n}\n')

def updated_leaf(prior,contract):
    _,_,start,_,_,rows,_,_=contract
    fields=prior[3]
    if fields[1]!=start or rows[0][0]!=start:raise ValueError('continuation leaf link')
    return leaf_render((*prior[:3],(fields[0],start,rows[0][1]),*prior[4:]))

def extend(directory,p):
    prior,contract=p
    old=prior[2];blocks,root,start,dst,*_=contract
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()) or set(blocks)-set(old)!={dst} or dst in live:
        raise ValueError('continuation fixture predecessor')
    expanded={**live,**blocks};check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=60)
    leaf=directory/'private_post_stm_sc_formatter_leaf.h'
    if leaf.read_text()!=leaf_render(prior):raise ValueError('continuation leaf header')
    next_leaf=updated_leaf(prior,contract)
    with (directory/'private_formatter_continuation.h').open('x') as out:out.write(render(contract))
    leaf.write_text(next_leaf)
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print('FORMATTER_CONTINUATION_FIXTURE verified=1 labels=10 new_roots=1')

def scope(d,e,sizes,p):
    prior,contract=p
    old=prior[2];blocks,root,_,dst,*_=contract
    if set(blocks)-set(old)!={dst} or any(sizes.get(a)!=4*len(blocks[a]) for a in (root,dst)):
        raise ValueError('continuation fixture extent')
    before={a:n for a,n in sizes.items() if a!=dst};before[root]=4*len(old[root])
    return check_spans({**dict(leaf_scope(d,e,before,prior)),root:sizes[root],dst:sizes[dst]})

def trace_entry(s,pc,w):
    label=r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n'
    pat=re.compile(label+r'    \+\+ctx\.inst_count;\n    formatter_continuation_before\(ctx,0x'+f'{pc:08x}u,0x{w:08x}u'+r'\);')
    hits=list(pat.finditer(s))
    if len(hits)!=1:raise ValueError('continuation entry trace')
    hit=hits[0];i=hit.start()+len(re.match(label,s[hit.start():])[0])
    line=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx); // original formatter continuation\n'
    if line in s:raise ValueError('continuation entry trace')
    return s[:i]+line+s[i:]

def install(directory,p):
    _,contract=p
    _,root,start,dst,word,rows,*_=contract
    files=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in files}
    main=directory/'main_output.cpp';main_text=main.read_text()
    expected={pc:(root,w) for pc,w in rows}
    audit_native(sources.values(),main_text,{**expected,dst:(dst,word)})
    owners=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{root:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(owners)!=1:raise ValueError('continuation native owner')
    body=exact_function(owners[0],root);verify_direct(body,rows[-1][0],dst)
    main_text,_=ensure_resume(main_text,body,root,start)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('continuation native hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','formatter_continuation_before'))
            if pc==start:s=trace_entry(s,pc,w)
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('continuation native hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid formatter_continuation_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('continuation native coverage')
    for file,s in changed.items():file.write_text(s)
    main.write_text(main_text)
    print('FORMATTER_CONTINUATION_TRANSLATION verified=1 labels=10 direct_call=1 outer_resume=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','continuation leaf link','continuation fixture predecessor','continuation leaf header','continuation fixture extent','continuation entry trace','continuation native owner','continuation native hook','continuation native coverage'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes()
        with plan_cache_scope():
            p=plan(d,e,details=True)
            if q.fixture:extend(q.fixture,p);return 0
            if q.install:install(q.install,p);return 0
            if q.analyzer:
                if not q.symbols:raise ValueError('continuation fixture extent')
                q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
                print('FORMATTER_CONTINUATION_ANALYZER verified=1 expanded_root=1 new_roots=1');return 0
            if not render(p[1]) or not updated_leaf(*p):raise ValueError('continuation leaf header')
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_CONTINUATION_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('FORMATTER_CONTINUATION_PREP verified=1 labels=10 guarded_return=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
