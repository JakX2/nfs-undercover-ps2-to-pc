#!/usr/bin/env python3
"""Install read-only profiling instruction hooks in the private translation."""
import argparse
import re
import struct
from pathlib import Path
from prepare_ipc_profile_geometry import derive, layout, CALL, HELPER
from prepare_v419_full_start import MAX_DOL
from make_private_elf_symbol_map import HEADER, parse_functions
from make_v624_ipc_geometry import exact_words
from make_v651_open_fixture import SUBMIT
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v1337_open_completion import hook_submit

def plan(d,e):
    _,labels,*_=derive(d,e)
    words=exact_words(d,e,HELPER,parse_functions(e)[HELPER]//4)
    if labels!=len(words):raise ValueError('profile unreachable labels')
    return words,layout(d,e),exact_words(d,e,CALL,2)

def render(p):
    words,ranges,edge=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    rows=','.join('undercover::wii::IpcProfileNativeWord{'+fmt((HELPER+4*i,w))+'}' for i,w in enumerate(words))
    objects=','.join('undercover::wii::AllocatorRange{'+fmt(row)+'}' for row in ranges)
    return ('#pragma once\n#include "wii_ipc_profile_execution.h"\nnamespace ipc_profile {\n'
        f'inline constexpr std::array<undercover::wii::IpcProfileNativeWord,{len(words)}> words'+'{'+rows+'};\n'
        'inline constexpr undercover::wii::IpcProfileExecutionExpectation expected{'+fmt((HELPER,CALL,*edge))+
        ',words,undercover::wii::IpcProfileLayout{'+objects+'}};\n}\n')

def install(root,p):
    words,_,edge=p
    sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    expected={HELPER+4*i:(HELPER,w) for i,w in enumerate(words)}
    expected.update({CALL:(SUBMIT,edge[0]),CALL+4:(SUBMIT,edge[1])})
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),expected)
    callers=[s for s in sources.values() if f'loc_{CALL:X}: ;' in s]
    if len(callers)!=1:raise ValueError('profile caller')
    verify_direct(callers[0],CALL,HELPER)
    trace=f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{HELPER:X}) nwii::runtime::trace_call(0x{HELPER:X}, ctx);'
    if sum(s.count(trace) for s in sources.values())!=1:raise ValueError('profile entry trace')
    seen=set();returns=0;changes={}
    for path,s in sources.items():
        old=s
        for i,w in enumerate(words):
            pc=HELPER+4*i
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in seen or s.count(hook)!=1:raise ValueError('profile hook')
            seen.add(pc);s=s.replace(hook,hook.replace('v1344_before','ipc_profile_before'))
        pc=CALL+4
        if f'loc_{pc:X}: ;' in s:
            # Earlier opens pass through with no active witness.
            pattern=(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {edge[1]:08X}'+
                     r'\n(?=    \+\+ctx\.inst_count;)')
            if len(re.findall(pattern,s))!=1:raise ValueError('profile return hook')
            s=re.sub(pattern,lambda m:m[0]+f'    ipc_profile_return(ctx,0x{pc:08x}u);\n',s,count=1)
            returns+=1
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('profile include')
            changes[path]=s.replace(anchor,anchor+'\nvoid ipc_profile_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);\nvoid ipc_profile_return(nwii::runtime::CPUContext&,uint32_t);')
    if len(seen)!=len(words) or returns!=1:raise ValueError('profile hook coverage')
    for path,s in changes.items():path.write_text(s)
    print(f'IPC_PROFILE_TRANSLATION verified=1 labels={len(seen)} direct_edges=1 return_hooks=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not HEADER.size<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.out,p)
        else:
            with (q.out/'private_ipc_profile.h').open('x') as f:f.write(render(p))
            print(f'IPC_PROFILE_PRIVATE verified=1 labels={len(p[0])} objects=4')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','identity','profile unreachable labels','profile caller','profile entry trace','profile hook','profile return hook',
                 'profile include','profile hook coverage','completion hook label','native IPC duplicate root','native IPC label identity',
                 'native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge'}
        print('IPC_PROFILE_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_geometry_or_io'))
        return 1
if __name__=='__main__':raise SystemExit(main())
