#!/usr/bin/env python3
"""Private async submit return geometry and local continuation hook."""
import argparse
import re
import struct
from pathlib import Path
from prepare_ipc_dispatch_native import plan as prior
from prepare_v1337_open_completion import plan as completion,RESTORE
from prepare_v1385_async_ioctl_geometry import plan as wrapper_plan,IOCTL,EDGES
from make_v651_open_fixture import SUBMIT
from make_start_to_ipc_submit_v72 import EDGES as SUBMIT_EDGES
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_owner_scheduler_v722 import reachable
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct

def corridor(root,words,start,call,helper):
    end=root+4*len(words);work=[(start,False)];seen=set();returns=set();labels=set();edges=set()
    while work:
        pc,restored=work.pop()
        if (pc,restored) in seen:continue
        if not start<=pc<end or pc&3:continue
        seen.add((pc,restored));labels.add(pc)
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op==18 and w&1:
            if pc==call and not restored and direct_bl(w,pc)==helper:
                edges.add(pc);work.append((pc+4,True))
            continue
        if op==19 and xo==16:
            if w&1:raise ValueError('async return link')
            if restored:returns.add(pc)
            if ((w>>21)&20)!=20:work.append((pc+4,restored))
            continue
        if op==17 or (op==19 and xo in (50,528)) or (op==31 and xo==146):continue
        if op in (16,18):
            if w&3:raise ValueError('async return branch')
            m,s=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            dst=pc+(((w&m)^s)-s)
            work.append((dst,restored))
            if op==18 or ((w>>21)&20)==20:continue
        work.append((pc+4,restored))
    if edges!={call} or not returns:raise ValueError('async return corridor')
    return labels,returns

def plan(d,e):
    _,start,*_=prior(d,e)
    shared,*_=completion(d,e)
    body=shared[SUBMIT];restore=shared[RESTORE]
    call=SUBMIT_EDGES[10][0]
    if SUBMIT_EDGES[10][1]!=RESTORE:raise ValueError('async restore edge')
    labels,returns=corridor(SUBMIT,body,start,call,RESTORE)
    wrappers,*_=wrapper_plan(d,e)
    caller=EDGES[-2][0]+4
    if EDGES[-2][1]!=SUBMIT:raise ValueError('async caller edge')
    caller_word=wrappers[IOCTL][(caller-IOCTL)//4]
    words={pc:(SUBMIT,body[(pc-SUBMIT)//4]) for pc in range(start,SUBMIT+4*len(body),4)}
    words.update({pc:(RESTORE,restore[(pc-RESTORE)//4]) for pc in reachable(RESTORE,restore)})
    if len(returns)!=1 or sum(w>>26==31 and (w>>1)&1023==146 for w in restore)!=1:
        raise ValueError('async restore geometry')
    return start,caller,caller_word,(call,RESTORE,body[(call-SUBMIT)//4]),words,len(labels),len(returns)

def render(p):
    start,caller,word,edge,words,*_=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    rows=','.join('undercover::wii::IpcDispatchWord{'+fmt((owner,pc,w))+'}' for pc,(owner,w) in sorted(words.items()))
    return ('#pragma once\n#include "wii_async_submit_return.h"\nnamespace async_submit_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+rows+'};\n'
        'inline constexpr undercover::wii::AsyncSubmitReturnExpectation expected{'+fmt((SUBMIT,start,caller,word))+
        ',undercover::wii::IpcDispatchEdge{'+fmt(edge)+'},words};\n}\n')

def install(root,p):
    start,caller,w,edge,words,*_=p
    sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),{**words,caller:(IOCTL,w)})
    for pc,target in ((edge[0],edge[1]),(caller-4,SUBMIT)):
        hits=[s for s in sources.values() if f'loc_{pc:X}: ;' in s]
        if len(hits)!=1:raise ValueError('async return edge')
        verify_direct(hits[0],pc,target)
    for pc,(owner,word) in words.items():
        hook='v1344_before' if owner==SUBMIT else 'v1270_before'
        if sum(s.count(f'    {hook}(ctx,0x{pc:08x}u,0x{word:08x}u);') for s in sources.values())!=1:
            raise ValueError('async return prior hook')
    done=0
    changes={}
    for path,s in sources.items():
        raw=re.findall(r'(?mi)^loc_'+f'{caller:X}'+r': ;$',s)
        if not raw:continue
        pat=r'(?mi)^loc_'+f'{caller:X}'+r': ;\n    // 0x'+f'{caller:08X}: {w:08X}'+r'\n(?=    \+\+ctx\.inst_count;)'
        if len(raw)!=1 or len(re.findall(pat,s))!=1:raise ValueError('async caller hook')
        s=re.sub(pat,lambda m:m[0]+f'    async_submit_return(ctx,0x{caller:08x}u);\n',s,count=1)
        anchor='#include "runtime/cpu_context.h"'
        if s.count(anchor)!=1:raise ValueError('async include')
        changes[path]=s.replace(anchor,anchor+'\nvoid async_submit_return(nwii::runtime::CPUContext&,uint32_t);')
        done+=1
    if done!=1:raise ValueError('async caller hook')
    for path,s in changes.items():path.write_text(s)
    print(f'ASYNC_SUBMIT_TRANSLATION verified=1 labels={len(words)} return_hooks=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    allowed={'size','async return link','async return branch','async return corridor','async restore edge','async caller edge',
             'async restore geometry','async return edge','async return prior hook','async caller hook','async include',
             'native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
             'helper call label','helper direct native call','helper native return edge'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.out,p)
        else:
            with (q.out/'private_async_submit_return.h').open('x') as f:f.write(render(p))
            print(f'ASYNC_SUBMIT_PRIVATE verified=1 labels={len(p[4])} corridor={p[5]} returns={p[6]}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('ASYNC_SUBMIT_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
if __name__=='__main__':raise SystemExit(main())
