#!/usr/bin/env python3
"""Private native formatter first path, exact 704-byte frame and next callee."""
import argparse,re,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_resume_fixture import plan as resume_plan,scope as resume_scope
from prepare_post_stm_sc_report_formatter_path import plan as path_plan
from prepare_post_stm_sc_join import GUARD,check_spans
from prepare_v1337_open_completion import rebuild,hook_submit
from prepare_v419_full_start import MAX_DOL,words_at,direct_bl
from prepare_v1281_reply_fixture import symbols
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from make_v624_ipc_geometry import exact_words

def merge(old,root,ws,path,dst,word):
    if old.get(root)!=(ws[0],GUARD) or dst in old or len(path)!=23 or len(set(path))!=23 or path[0]!=root:
        raise ValueError('SC formatter predecessor')
    site=path[-1]
    if not root<=site<root+4*len(ws) or any(pc<root or pc>site or pc&3 for pc in path) or direct_bl(ws[(site-root)//4],site)!=dst:
        raise ValueError('SC formatter path')
    body=tuple(ws[(pc-root)//4] if pc in path else GUARD for pc in range(root,site+4,4))+(GUARD,)
    return {**old,root:body,dst:(word,GUARD)}

def saved_slots(mem,caller_sp,frame):
    saved=[]
    for at,v in sorted(mem.items()):
        if not caller_sp-frame<=at<caller_sp+8 or len(v)!=4 or v[0]!='part' or v[2:]!=(4,0):continue
        value=v[1]
        if value==('lr',0) and at==caller_sp+4:reg=32
        elif value[0]=='reg' and 14<=value[1]<=31:reg=value[1]
        else:continue
        if at&3 or any(mem.get(at+i)!=('part',value,4,i) for i in range(4)):raise ValueError('SC formatter saved slot')
        saved.append((at-caller_sp,reg))
    if len(saved)!=17 or len({r for _,r in saved})!=17 or (4,32) not in saved:raise ValueError('SC formatter saved slot count')
    return tuple(saved)

def plan(d,e):
    prior=resume_plan(d,e);old=prior[2]
    path,frame,accesses,saved,dst,gp,mem,ws=path_plan(d,e)
    root=path[0];caller=prior[4][-1][0]+4
    if root!=prior[3][3] or frame!=704 or saved!=16 or len(path)!=23 or len(accesses)!=5 or sum(k=='stack_write' for _,k,_,_ in accesses)!=4:
        raise ValueError('SC formatter ABI')
    caller_sp=-160
    slots=saved_slots(mem,caller_sp,frame)
    word=exact_words(d,e,dst,1)[0]
    blocks=merge(old,root,ws,path,dst,word)
    rows=tuple((pc,ws[(pc-root)//4]) for pc in path)
    sites=tuple((pc,n,at-caller_sp if k.startswith('stack') else at,k.startswith('stack'),k=='stack_write') for pc,k,n,at in accesses)
    return prior,old,blocks,(root,caller,dst,word,frame),rows,sites,slots

def render(p):
    _,_,_,fields,rows,sites,slots=p
    f=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    wr=','.join('undercover::wii::IpcDispatchWord{'+f((fields[0],pc,w))+'}' for pc,w in rows)
    ar=','.join('undercover::wii::ScFormatterAccess{'+f((pc,n))+','+str(at)+','+str(stack).lower()+','+str(wr).lower()+'}' for pc,n,at,stack,wr in sites)
    sr=','.join('undercover::wii::StmFinalSlot{'+str(at)+','+str(reg)+'u}' for at,reg in slots)
    return ('#pragma once\n#include "wii_post_stm_sc_formatter.h"\nnamespace post_stm_sc_formatter_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(rows)}> path'+'{'+wr+'};\n'
        f'inline constexpr std::array<undercover::wii::ScFormatterAccess,{len(sites)}> accesses'+'{'+ar+'};\n'
        f'inline constexpr std::array<undercover::wii::StmFinalSlot,{len(slots)}> slots'+'{'+sr+'};\n'
        'inline constexpr undercover::wii::ScFormatterExpectation expected{'+f(fields)+',path,accesses,slots};\n}\n')

def extend(directory,p):
    _,old,blocks,fields,rows,*_=p
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    live={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    if any(live.get(a)!=ws for a,ws in old.items()) or (set(blocks)-set(old))&set(live):raise ValueError('SC formatter predecessor')
    expanded={**live,**blocks};check_spans({a:4*len(ws) for a,ws in expanded.items()})
    new=rebuild(raw,expanded,max_roots=59)
    with (directory/'private_post_stm_sc_formatter.h').open('x') as out:out.write(render(p))
    image.write_bytes(new);csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(expanded.items())))
    print(f'POST_STM_SC_FORMATTER_FIXTURE verified=1 labels={len(rows)} new_roots=1 guarded_dependency=1')

def scope(d,e,sizes,p):
    prior,old,blocks,fields,*_=p;root,_,dst,*_=fields
    if set(blocks)-set(old)!={dst} or any(sizes.get(a)!=4*len(blocks[a]) for a in (root,dst)):raise ValueError('SC formatter extent')
    before={a:n for a,n in sizes.items() if a!=dst};before[root]=4*len(old[root])
    spans=dict(resume_scope(d,e,before,prior))
    return check_spans({**spans,root:sizes[root],dst:sizes[dst]})

def install(directory,p):
    _,_,_,fields,rows,*_=p;root,_,dst,word,_=fields
    paths=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    main=directory/'main_output.cpp'
    expected={pc:(root,w) for pc,w in rows}
    audit_native(sources.values(),main.read_text(),{**expected,dst:(dst,word)})
    owners=[s for s in sources.values() if re.search(r'(?mi)^void (?:fn|func)_'+f'{root:X}'+r'\(CPUContext& ctx\) \{',s)]
    if len(owners)!=1:raise ValueError('SC formatter owner')
    verify_direct(exact_function(owners[0],root),rows[-1][0],dst)
    done=set();changed={}
    for file,s in sources.items():
        old=s
        for pc,(_,w) in expected.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('SC formatter hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_formatter_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('SC formatter hook')
            changed[file]=s.replace(anchor,anchor+'\nvoid post_stm_sc_formatter_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(expected):raise ValueError('SC formatter coverage')
    for file,s in changed.items():file.write_text(s)
    print(f'POST_STM_SC_FORMATTER_TRANSLATION verified=1 labels={len(done)} direct_call=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','SC formatter predecessor','SC formatter path','SC formatter saved slot','SC formatter saved slot count','SC formatter ABI','SC formatter extent','SC formatter owner','SC formatter hook','SC formatter coverage','fixture geometry','fixture range','fixture overlap','completion roundtrip','completion hook label','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge','helper call label'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.fixture:extend(q.fixture,p);return 0
        if q.install:install(q.install,p);return 0
        if q.analyzer:
            if not q.symbols:raise ValueError('SC formatter extent')
            q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
            print('POST_STM_SC_FORMATTER_ANALYZER verified=1 expanded_root=1 new_roots=1');return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_FORMATTER_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('POST_STM_SC_FORMATTER_PREP verified=1 guarded_dependency=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
