#!/usr/bin/env python3
"""Private original post-allocation corridor and native hook installation."""
import argparse,struct
from pathlib import Path
from prepare_v1385_async_ioctl_geometry import plan,IOCTL,EDGES
from prepare_v1387_ioctl_allocation import RESUME
from prepare_v419_full_start import MAX_DOL
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v1337_open_completion import hook_submit
CALLS=EDGES[2:4]

def derive(d,e):
    roots,*_=plan(d,e);body=roots[IOCTL]
    words={pc:body[(pc-IOCTL)//4] for pc in range(RESUME,CALLS[-1][0]+4,4)}
    edges=[(dst,pc+4,words[pc],exact_words(d,e,dst,1)[0]) for pc,dst in CALLS]
    return words,edges

def refusal_geometry(p):
    # Classify the previously refused post-allocation store without
    # exposing its original word, effective address or register value.
    words,_=p;w=words[RESUME+4];op=w>>26;ra=(w>>16)&31
    base=1 if ra==1 else 2 if ra in (2,13) else 3 if ra else 0
    d=((w&0xffff)^0x8000)-0x8000
    direct=op in (36,37,38,39,44,45,47)
    disp=(0 if d<0 else 1 if d<=8 else 2 if d<=64 else 3) if direct else 4
    print(f'V1396_CONSTRUCTION_STORE_GEOMETRY ordinal=24 direct_store={int(direct)} base_class={base} displacement_class={disp}')

def render(p):
    words,edges=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    return ('#pragma once\n#include "wii_ioctl_construction_v1392.h"\nnamespace v1392 {\n'
      'inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(words))+'> words{'+
      ','.join('undercover::wii::ReplyNativeWord{'+fmt((IOCTL,pc,w))+'}' for pc,w in words.items())+'};\n'
      'inline constexpr undercover::wii::IoctlConstructionExpectation expected{'+fmt((IOCTL,RESUME))+','+
      ','.join('undercover::wii::VectorEdge{'+fmt(row)+'}' for row in edges)+',words};\n}\n')

def install(root,p):
    words,edges=p;sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),{pc:(IOCTL,w) for pc,w in words.items()})
    for site,dst in CALLS:
        owners=[s for s in sources.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('construction edge')
        verify_direct(owners[0],site,dst)
    prior=f'    v1387_before(ctx,0x{RESUME:08x}u,0x{words[RESUME]:08x}u);'
    if sum(s.count(prior) for s in sources.values())!=1:raise ValueError('construction resume hook')
    wanted={pc:w for pc,w in words.items() if pc!=RESUME};done=set();changes={}
    for path,s in sources.items():
        old=s
        for pc,w in wanted.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            if pc in done:raise ValueError('construction hook')
            done.add(pc)
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if s.count(hook)!=1:raise ValueError('construction hook')
            s=s.replace(hook,hook.replace('v1344_before','v1392_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('construction hook')
            changes[path]=s.replace(anchor,anchor+'\nvoid v1392_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(wanted):raise ValueError('construction hook coverage')
    for path,s in changes.items():path.write_text(s)
    print(f'V1392_CONSTRUCTION_TRANSLATION verified=1 labels={len(words)} direct_edges=2')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=derive(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.out,p);return 0
        with (q.out/'v1392_private_ioctl_construction.h').open('x') as f:f.write(render(p))
        print(f'V1392_CONSTRUCTION_GEOMETRY verified=1 labels={len(p[0])}')
        refusal_geometry(p)
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','construction edge','construction resume hook','construction hook','construction hook coverage',
            'completion hook label','native IPC duplicate root','native IPC label identity','native IPC label body',
            'native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge'}
        print('V1392_CONSTRUCTION_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
