#!/usr/bin/env python3
"""Private bridge from the stronger STM lane to the previously verified SC startup."""
import argparse
import struct
from pathlib import Path
from prepare_stm_final_return import plan as final_plan,prologue
from restore_post_stm_v89 import OS_CALL,ROOT,SIZE,EDGES
from prepare_v1337_open_completion import plan as completion,DISABLE
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_v1377_stm_tail import scan
from audit_osinit_suffix_v929 import first_region,category
from prepare_v419_full_start import words_at
from prepare_v1281_reply_fixture import symbols
from prepare_v1337_open_completion import rebuild,hook_submit
from prepare_v1386_ioctl_prefix import scope as prior_scope,check_spans
from prepare_v1385_async_ioctl_geometry import plan as ioctl_plan
from prepare_v1270_ipc_epilogue import analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
GUARD=0x44000002

def prefix(root,words,site,target):
    rows,backs,stores,stops=first_region(root,words,root)
    if backs or len(stops)!=1 or stops[0]!=(site,1,1,target) or set(rows)!=set(range(root,site+4,4)):
        raise ValueError('SC first boundary')
    for pc,w in rows.items():
        op=w>>26;ra=(w>>16)&31
        if pc==site:continue
        kind=category(w)
        if kind=='store':
            if op not in (36,37,47) or ra!=1:raise ValueError('SC first store')
        elif kind=='load':
            if op not in (32,46) or ra!=1:raise ValueError('SC first load')
        elif kind!='integer':raise ValueError('SC first opcode')
    frame,saved=prologue(tuple(rows[pc] for pc in range(root,site,4)))
    if not frame or 'lr' not in saved.values():raise ValueError('SC frame')
    return len(rows),stores,len(saved)-1

def plan(d,e):
    fields,_,_,_,_,_=final_plan(d,e)
    if fields[2]!=OS_CALL or direct_bl(fields[3],OS_CALL)!=ROOT:
        raise ValueError('SC caller')
    if parse_functions(e).get(ROOT)!=SIZE:raise ValueError('SC extent')
    body=exact_words(d,e,ROOT,SIZE//4)
    if body[-1]!=0x4e800020:raise ValueError('SC return')
    reachable,calls,returns,_,_=scan(ROOT,body,ROOT,dict(EDGES))
    if calls!=set(EDGES) or len(returns)!=1:raise ValueError('SC call closure')
    site,target=EDGES[0]
    shared,*_=completion(d,e)
    if target!=DISABLE or tuple(shared[DISABLE])!=tuple(exact_words(d,e,DISABLE,len(shared[DISABLE]))):
        raise ValueError('SC shared helper')
    labels,stores,saved=prefix(ROOT,body,site,target)
    frame,slots=prologue(body[:labels-1])
    words={OS_CALL:(OS_CALL,fields[3]),**{ROOT+4*i:(ROOT,w) for i,w in enumerate(body[:labels])}}
    return (OS_CALL,ROOT,target,shared[DISABLE][0],frame),slots,words,(len(reachable),len(calls),labels,stores,saved)

def derive(d,e):return plan(d,e)[3]

def blocks_for(p):
    fields,_,words,_=p
    return {a:tuple(w for _,(owner,w) in sorted(words.items()) if owner==a)+(GUARD,)
            for a in fields[:2]}

def render(p):
    fields,slots,words,_=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    sr=','.join('undercover::wii::StmFinalSlot{'+str(off)+','+str(32 if reg=='lr' else reg)+'u}' for off,reg in sorted(slots.items()))
    wr=','.join('undercover::wii::IpcDispatchWord{'+fmt((owner,pc,w))+'}' for pc,(owner,w) in sorted(words.items()))
    return ('#pragma once\n#include "wii_post_stm_sc_entry.h"\nnamespace post_stm_sc_private {\n'
        f'inline constexpr std::array<undercover::wii::StmFinalSlot,{len(slots)}> slots'+'{'+sr+'};\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+wr+'};\n'
        'inline constexpr undercover::wii::PostStmScExpectation expected{'+fmt(fields)+',slots,words};\n}\n')

def extend(directory,p):
    image=directory/'fixture.dol';csv=directory/'symbols.csv';raw=image.read_bytes()
    old={a:words_at(raw,a,n//4) for a,n in symbols(csv.read_text()).items()}
    extra=blocks_for(p)
    if set(old)&set(extra):raise ValueError('SC root conflict')
    blocks={**old,**extra}
    check_spans({a:4*len(ws) for a,ws in blocks.items()})
    if len(blocks)+2>53:raise ValueError('SC root cap')
    new=rebuild(raw,blocks,max_roots=53)
    with (directory/'private_post_stm_sc.h').open('x') as out:out.write(render(p))
    image.write_bytes(new)
    csv.write_text('Name,Location,Size\n'+''.join(f'func_{a:08X},{a:08x},{4*len(ws)}\n' for a,ws in sorted(blocks.items())))
    print('POST_STM_SC_FIXTURE verified=1 new_roots=2 original_labels=6 explicit_guards=2')

def scope(d,e,sizes,p):
    extra={a:4*len(ws) for a,ws in blocks_for(p).items()}
    if any(sizes.get(a)!=n for a,n in extra.items()):raise ValueError('SC root extent')
    old={a:n for a,n in sizes.items() if a not in extra}
    prior=dict(prior_scope(d,e,old,ioctl_plan(d,e)[0]))
    if set(prior)&set(extra):raise ValueError('SC root conflict')
    return check_spans({**prior,**extra})

def install(directory,p):
    fields,_,words,_=p
    paths=sorted(directory.glob('output_*.cpp'));sources={x:x.read_text() for x in paths}
    audit_native(sources.values(),(directory/'main_output.cpp').read_text(),words)
    site=max(pc for pc,(owner,_) in words.items() if owner==fields[1])
    for pc,dst in ((fields[0],fields[1]),(site,fields[2])):
        owners=[s for s in sources.values() if f'loc_{pc:X}: ;' in s]
        if len(owners)!=1:raise ValueError('SC edge owner')
        verify_direct(owners[0],pc,dst)
    done=set();changed={}
    for path,s in sources.items():
        old=s
        for pc,(_,w) in words.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('SC hook identity')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','post_stm_sc_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('SC hook include')
            changed[path]=s.replace(anchor,anchor+'\nvoid post_stm_sc_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(words):raise ValueError('SC hook coverage')
    for path,s in changed.items():path.write_text(s)
    print(f'POST_STM_SC_TRANSLATION verified=1 original_labels={len(done)} direct_edges=2')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--fixture',type=Path);m.add_argument('--install',type=Path);m.add_argument('--analyzer',type=Path)
    a.add_argument('--symbols',type=Path);q=a.parse_args()
    safe={'size','SC caller','SC extent','SC return','SC call closure','SC shared helper','SC first boundary',
          'SC first store','SC first load','SC first opcode','SC frame','tail extent','tail escape','tail call','tail control',
          'tail reachability','prologue identity','prologue slot','prologue frame','region coverage','unsupported boundary',
          'SC root conflict','SC root cap','SC root extent','SC edge owner','SC hook identity','SC hook include','SC hook coverage',
          'fixture geometry','fixture range','fixture overlap','completion roundtrip','completion hook label','prefix ownership','prefix extent',
          'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
          'helper direct native call','helper native return edge','helper call label'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:
            raise ValueError('size')
        d,e=q.dol.read_bytes(),q.elf.read_bytes();p=plan(d,e)
        if q.fixture:extend(q.fixture,p);return 0
        if q.install:install(q.install,p);return 0
        if q.analyzer:
            if not q.symbols:raise ValueError('SC root extent')
            q.analyzer.write_text(analyzer(q.analyzer.read_text(),scope(d,e,symbols(q.symbols.read_text()),p)))
            print('POST_STM_SC_ANALYZER verified=1 additional_roots=2');return 0
        reachable,calls,labels,stores,saved=p[3]
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_JOIN_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_JOIN_GEOMETRY verified=1 original_caller=1 subsystem_labels={reachable} direct_edges={calls} first_labels={labels} stack_stores={stores} saved_gprs={saved} shared_disable=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
