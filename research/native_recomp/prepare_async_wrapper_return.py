#!/usr/bin/env python3
"""Private read-only async IOCTL epilogue geometry, including the compiler restore leaf."""
import argparse
import hashlib
import re
import struct
from pathlib import Path
from prepare_v1385_async_ioctl_geometry import plan as wrapper_plan,IOCTL,EDGES
from prepare_v1383_stm_ioctl_entry import CALL as STM_CALL,STM
from prepare_v419_full_start import MAX_DOL,OWNER_SHA,direct_bl
from make_private_elf_symbol_map import ORIGINAL_SHA256
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v1337_open_completion import hook_submit

def corridor(root,words,start,call,helper):
    end=root+4*len(words);seen=set();labels=set();returns=set();work=[(start,False)]
    while work:
        pc,restored=work.pop()
        if (pc,restored) in seen:continue
        if not start<=pc<end or pc&3:raise ValueError('wrapper extent')
        seen.add((pc,restored));labels.add(pc)
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op==18 and w&1:
            if restored or pc!=call or direct_bl(w,pc)!=helper:raise ValueError('wrapper call')
            work.append((pc+4,True));continue
        if w==0x4e800020:
            if not restored:raise ValueError('wrapper early return')
            returns.add(pc);continue
        if op in (16,18):
            if w&3:raise ValueError('wrapper branch')
            m,s=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            target=pc+(((w&m)^s)-s)
            if target<=pc:raise ValueError('wrapper loop')
            work.append((target,restored))
            if op==18 or ((w>>21)&20)==20:continue
        elif op==32:
            if (w>>21)&31:raise ValueError('wrapper stack load')
        elif op==31 and xo==467:
            if ((w>>16)&31)|(((w>>11)&31)<<5)!=8:raise ValueError('wrapper special register')
        elif not (op in (10,11,14,15,20,21,23,24,25,26,27,28,29) or
                  (op==31 and xo in (0,32,28,444,266,316))):
            raise ValueError('wrapper opcode')
        work.append((pc+4,restored))
    if len(returns)!=1 or call not in labels:raise ValueError('wrapper route')
    return labels,returns

def plan(d,e):
    if hashlib.sha256(d).hexdigest()!=OWNER_SHA or hashlib.sha256(e).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError('identity')
    roots,_,_,_,_,_,leaf,_,_=wrapper_plan(d,e)
    start=EDGES[-2][0]+4;call,helper=EDGES[-1]
    labels,returns=corridor(IOCTL,roots[IOCTL],start,call,helper)
    caller=STM_CALL+4;caller_word=exact_words(d,e,caller,1)[0]
    if direct_bl(exact_words(d,e,STM_CALL,1)[0],STM_CALL)!=IOCTL:raise ValueError('wrapper caller')
    ws=roots[helper];count=leaf[1]
    if len(ws)!=count+1 or ws[-1]!=0x4e800020:raise ValueError('wrapper leaf extent')
    rows={pc:(IOCTL,roots[IOCTL][(pc-IOCTL)//4]) for pc in labels}
    rows.update({helper+4*i:(helper,w) for i,w in enumerate(ws)})
    return start,caller,caller_word,count,(call,helper,roots[IOCTL][(call-IOCTL)//4]),rows,len(labels),len(returns)

def render(p):
    start,caller,word,count,edge,words,*_=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    rows=','.join('undercover::wii::IpcDispatchWord{'+fmt((owner,pc,w))+'}' for pc,(owner,w) in sorted(words.items()))
    return ('#pragma once\n#include "wii_async_wrapper_return.h"\nnamespace async_wrapper_private {\n'
        f'inline constexpr std::array<undercover::wii::IpcDispatchWord,{len(words)}> words'+'{'+rows+'};\n'
        'inline constexpr undercover::wii::AsyncWrapperReturnExpectation expected{'+fmt((IOCTL,start,caller,word,count))+
        ',undercover::wii::IpcDispatchEdge{'+fmt(edge)+'},words};\n}\n')

def install(root,p):
    start,caller,w,count,edge,words,*_=p
    sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),{**words,caller:(STM,w)})
    for pc,target in ((edge[0],edge[1]),(caller-4,IOCTL)):
        hits=[s for s in sources.values() if f'loc_{pc:X}: ;' in s]
        if len(hits)!=1:raise ValueError('wrapper native edge')
        verify_direct(hits[0],pc,target)
    done=set();returned=0;changes={}
    for path,s in sources.items():
        old=s
        for pc,(_,word) in words.items():
            if pc==start:
                raw=re.findall(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s)
                if not raw:continue
                a=(f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {word:08X}\n'
                   f'    async_submit_return(ctx,0x{pc:08x}u);\n    ++ctx.inst_count;\n')
                if len(raw)!=1 or s.count(a)!=1:raise ValueError('wrapper prior return hook')
                s=s.replace(a,a+f'    async_wrapper_before(ctx,0x{pc:08x}u,0x{word:08x}u);\n')
            else:
                s,found=hook_submit(s,pc,word)
                if not found:continue
                a=f'    v1344_before(ctx,0x{pc:08x}u,0x{word:08x}u);'
                if s.count(a)!=1:raise ValueError('wrapper native hook')
                s=s.replace(a,a.replace('v1344_before','async_wrapper_before'))
            if pc in done:raise ValueError('wrapper duplicate hook')
            done.add(pc)
        raw=re.findall(r'(?mi)^loc_'+f'{caller:X}'+r': ;$',s)
        if raw:
            pat=r'(?mi)^loc_'+f'{caller:X}'+r': ;\n    // 0x'+f'{caller:08X}'+': '+f'{w:08X}'+r'\n(?=    \+\+ctx\.inst_count;)'
            if len(raw)!=1 or len(re.findall(pat,s))!=1:raise ValueError('wrapper caller hook')
            s=re.sub(pat,lambda m:m[0]+f'    async_wrapper_return(ctx,0x{caller:08x}u);\n',s,count=1)
            returned+=1
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('wrapper include')
            changes[path]=s.replace(anchor,anchor+'\nvoid async_wrapper_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);\nvoid async_wrapper_return(nwii::runtime::CPUContext&,uint32_t);')
    if done!=set(words) or returned!=1:raise ValueError('wrapper hook coverage')
    for path,s in changes.items():path.write_text(s)
    print(f'ASYNC_WRAPPER_TRANSLATION verified=1 labels={len(done)} return_hooks=1')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('--out',type=Path);a.add_argument('--install',type=Path);q=a.parse_args()
    allowed={'size','identity','wrapper extent','wrapper call','wrapper early return','wrapper branch','wrapper loop',
             'wrapper stack load','wrapper special register','wrapper opcode','wrapper route','wrapper caller','wrapper leaf extent',
             'wrapper native edge','wrapper prior return hook','wrapper native hook','wrapper duplicate hook','wrapper caller hook',
             'wrapper include','wrapper hook coverage','completion hook label','native IPC duplicate root','native IPC label identity',
             'native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=plan(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.install,p);return 0
        if q.out:
            with (q.out/'private_async_wrapper_return.h').open('x') as f:f.write(render(p))
        print(f'ASYNC_WRAPPER_GEOMETRY verified=1 labels={len(p[5])} wrapper_labels={p[6]} restore_gprs={p[3]} returns={p[7]}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('ASYNC_WRAPPER_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
if __name__=='__main__':raise SystemExit(main())
