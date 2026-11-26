#!/usr/bin/env python3
"""Authenticate private original wrapper continuation after both flush calls."""
import argparse,struct,re
from pathlib import Path
from prepare_v1385_async_ioctl_geometry import plan,IOCTL,EDGES
from prepare_v419_full_start import MAX_DOL
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v1337_open_completion import hook_submit
CALLS=EDGES[3:5]
START=EDGES[2][0]+4
SECOND=EDGES[3][0]+4

def derive(d,e):
    roots,*_=plan(d,e);body=roots[IOCTL]
    words={pc:body[(pc-IOCTL)//4] for pc in range(START,CALLS[-1][0]+4,4)}
    edges=[(dst,pc+4,words[pc],exact_words(d,e,dst,1)[0]) for pc,dst in CALLS]
    return words,edges

def render(p):
    words,edges=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    return ('#pragma once\n#include "wii_ioctl_flush_tail_v1401.h"\nnamespace v1401 {\n'
      'inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(words))+'> words{'+
      ','.join('undercover::wii::ReplyNativeWord{'+fmt((IOCTL,pc,w))+'}' for pc,w in words.items())+'};\n'
      'inline constexpr undercover::wii::IoctlFlushTailExpectation expected{'+
      ','.join('undercover::wii::VectorEdge{'+fmt(row)+'}' for row in edges)+',words};\n}\n')

def install(root,p):
    words,edges=p;sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),{pc:(IOCTL,w) for pc,w in words.items()})
    for site,dst in CALLS:
        owners=[s for s in sources.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('output edge')
        verify_direct(owners[0],site,dst)
    for pc,w in words.items():
        if pc>=SECOND:continue
        hook=f'    v1392_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
        if sum(s.count(hook) for s in sources.values())!=1:raise ValueError('output prior hook')
    done=set();changed={}
    for path,s in sources.items():
        old=s
        for pc,w in words.items():
            if pc<SECOND:continue
            if pc==SECOND:
                if f'loc_{pc:X}: ;' not in s:continue
                anchor=(f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'
                    f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V625 IPC client return\n'
                    '    ++ctx.inst_count;\n')
                if s.count(anchor)!=1:raise ValueError('output resume hook')
                s=s.replace(anchor,anchor+f'    v1392_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n')
            else:
                s,found=hook_submit(s,pc,w)
                if not found:continue
                hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
                if s.count(hook)!=1:raise ValueError('output hook')
                s=s.replace(hook,hook.replace('v1344_before','v1392_before'))
            if pc in done:raise ValueError('output hook coverage')
            done.add(pc)
        if s!=old:
            if 'void v1392_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);' not in s:
                anchor='#include "runtime/cpu_context.h"'
                if s.count(anchor)!=1:raise ValueError('output hook')
                s=s.replace(anchor,anchor+'\nvoid v1392_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
            changed[path]=s
    if done!={pc for pc in words if pc>=SECOND}:raise ValueError('output hook coverage')
    for path,s in changed.items():path.write_text(s)
    print(f'V1401_OUTPUT_TRANSLATION verified=1 labels={len(words)} direct_edges=2')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=derive(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.out,p);return 0
        with (q.out/'v1401_private_ioctl_output.h').open('x') as f:f.write(render(p))
        print(f'V1401_OUTPUT_GEOMETRY verified=1 labels={len(p[0])}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','output edge','output prior hook','output resume hook','output hook','output hook coverage',
            'completion hook label','native IPC duplicate root','native IPC label identity','native IPC label body',
            'native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge'}
        print('V1401_OUTPUT_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
