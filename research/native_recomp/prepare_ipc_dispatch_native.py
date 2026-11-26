#!/usr/bin/env python3
"""Authenticate and instrument the private original IPC dispatch lane."""
import argparse
import re
import struct
from pathlib import Path
from prepare_ipc_dispatch_geometry import derive,credit_object
from prepare_ipc_profile_geometry import layout
from prepare_v1414_ipc_ring import ring_object
from prepare_v419_full_start import MAX_DOL
from make_private_elf_symbol_map import HEADER,parse_functions
from make_v624_ipc_geometry import exact_words
from make_v651_open_fixture import submit_geometry,SUBMIT
from make_start_to_ipc_submit_v72 import EDGES
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v1337_open_completion import hook_submit

def helper_shape(words,write):
    if not 2<=len(words)<=16 or words[-1]!=0x4e800020:raise ValueError('dispatch helper shape')
    accesses=[]
    for i,w in enumerate(words[:-1]):
        op=w>>26;xo=(w>>1)&1023
        if op==36 or (op==31 and xo==151):accesses.append((i,True))
        elif op==32 or (op==31 and xo==23):accesses.append((i,False))
        elif op in (16,17,18,19,33,34,35,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,60,61):
            raise ValueError('dispatch helper instruction')
        elif op==31 and xo in (55,87,119,150,183,215,247,279,311,343,375,407,439,467,533,534,535,567,597,599,631,661,662,663,695,725,727,759,790,918,983,1014,146):
            raise ValueError('dispatch helper instruction')
    if len(accesses)!=1 or accesses[0][1]!=write:raise ValueError('dispatch helper access')
    return accesses[0][0]

def plan(d,e):
    derive(d,e)
    roots,_=submit_geometry(d,e)
    start=EDGES[3][0]+4
    calls=tuple(EDGES[6:9])
    stop=calls[-1][0]+4
    sizes=parse_functions(e)
    body=roots[SUBMIT]
    words={pc:(SUBMIT,body[(pc-SUBMIT)//4]) for pc in range(start,stop+4,4)}
    for _,target in calls:
        if target in roots:ws=roots[target]
        else:
            size=sizes.get(target,0)
            if not 8<=size<=64 or size&3:raise ValueError('dispatch helper extent')
            ws=exact_words(d,e,target,size//4)
        helper_shape(ws,target==calls[0][1])
        words.update({target+4*i:(target,w) for i,w in enumerate(ws)})
    edges=tuple((pc,target,words[pc][1]) for pc,target in calls)
    return (start,stop,words,edges,ring_object(d,e),credit_object(d,e),layout(d,e))

def render(p):
    start,stop,words,edges,ring,credit,profile=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    rows=','.join('undercover::wii::IpcDispatchWord{'+fmt((owner,pc,w))+'}' for pc,(owner,w) in sorted(words.items()))
    calls=','.join('undercover::wii::IpcDispatchEdge{'+fmt(row)+'}' for row in edges)
    objs=','.join('undercover::wii::AllocatorRange{'+fmt(x)+'}' for x in profile)
    return ('#pragma once\n#include "wii_ipc_dispatch_execution.h"\nnamespace ipc_dispatch_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+rows+'};\n'
        'inline constexpr undercover::wii::IpcDispatchExpectation expected{'+fmt((SUBMIT,start,stop))+
        ',{{'+calls+'}},words,undercover::wii::AllocatorRange{'+fmt(ring[:2])+'},undercover::wii::AllocatorRange{'+
        fmt(credit)+'},'+str(ring[2])+'u,undercover::wii::IpcProfileLayout{'+objs+'}};\n}\n')

def install(root,p):
    start,stop,words,edges,*_=p
    sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),words)
    returns={pc+4:words[pc+4][1] for pc,_,_ in edges}
    for pc,target,_ in edges:
        hits=[s for s in sources.values() if f'loc_{pc:X}: ;' in s]
        if len(hits)!=1:raise ValueError('dispatch caller')
        verify_direct(hits[0],pc,target)
        trace=f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{target:X}) nwii::runtime::trace_call(0x{target:X}, ctx);'
        if sum(s.count(trace) for s in sources.values())!=1:raise ValueError('dispatch entry trace')
    for pc,(owner,w) in words.items():
        if owner!=SUBMIT:continue
        hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
        if sum(s.count(hook) for s in sources.values())!=1:raise ValueError('dispatch prior hook')
    done=set();returned=set();changes={}
    for path,s in sources.items():
        old=s
        for pc,(owner,w) in words.items():
            if owner==SUBMIT:continue
            s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('dispatch hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','ipc_dispatch_before'))
        for pc,w in returns.items():
            raw=re.findall(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s)
            if not raw:continue
            pat=r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n(?=    \+\+ctx\.inst_count;)'
            if pc in returned or len(raw)!=1 or len(re.findall(pat,s))!=1:raise ValueError('dispatch return hook')
            s=re.sub(pat,lambda m:m[0]+f'    ipc_dispatch_return(ctx,0x{pc:08x}u);\n',s,count=1)
            returned.add(pc)
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('dispatch include')
            changes[path]=s.replace(anchor,anchor+'\nvoid ipc_dispatch_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);\nvoid ipc_dispatch_return(nwii::runtime::CPUContext&,uint32_t);')
    if done!={pc for pc,(owner,_) in words.items() if owner!=SUBMIT} or returned!=set(returns):
        raise ValueError('dispatch hook coverage')
    for path,s in changes.items():path.write_text(s)
    print(f'IPC_DISPATCH_TRANSLATION verified=1 labels={len(words)} helper_labels={len(done)} edges=3 returns=3')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    allowed={'size','identity','dispatch helper shape','dispatch helper instruction','dispatch helper access','dispatch helper extent',
             'dispatch caller','dispatch entry trace','dispatch prior hook','dispatch hook','dispatch return hook','dispatch include',
             'dispatch hook coverage','completion hook label','native IPC duplicate root','native IPC label identity','native IPC label body',
             'native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not HEADER.size<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.out,p)
        else:
            with (q.out/'private_ipc_dispatch.h').open('x') as f:f.write(render(p))
            print(f'IPC_DISPATCH_PRIVATE verified=1 labels={len(p[2])} edges=3')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('IPC_DISPATCH_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_geometry_or_io'))
        return 1
if __name__=='__main__':raise SystemExit(main())
