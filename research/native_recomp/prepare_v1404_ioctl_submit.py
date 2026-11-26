#!/usr/bin/env python3
"""Authenticate original asynchronous submit prefix and queue helper."""
import argparse,struct
from pathlib import Path
from prepare_v1385_async_ioctl_geometry import plan,IOCTL,EDGES
from make_v651_open_fixture import submit_geometry,SUBMIT
from make_start_to_ipc_submit_v72 import EDGES as SUBMIT_EDGES
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_v624_ipc_geometry import exact_words
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v1337_open_completion import hook_submit
CALLS=SUBMIT_EDGES[:2]
QUEUE=CALLS[0][1]
WRAPPER=EDGES[4]
def derive(d,e):
    wrapper,*_=plan(d,e);roots,_=submit_geometry(d,e)
    if WRAPPER[1]!=SUBMIT:raise ValueError('submit wrapper edge')
    queue=roots[QUEUE]
    if len(queue)!=4 or queue[-1]!=0x4e800020 or sum(w>>26==36 for w in queue)!=2 or sum(w>>26==14 for w in queue)!=1:
        raise ValueError('submit queue shape')
    prefix=roots[SUBMIT][:(CALLS[1][0]-SUBMIT)//4+1]
    if {SUBMIT+4*i:direct_bl(w,SUBMIT+4*i) for i,w in enumerate(prefix) if w>>26==18 and w&3==1}!=dict(CALLS):
        raise ValueError('submit prefix edges')
    ws={SUBMIT:prefix,QUEUE:queue}
    rows=[(dst,site+4,exact_words(d,e,site,1)[0],exact_words(d,e,dst,1)[0]) for site,dst in (WRAPPER,*CALLS)]
    return ws,rows
def render(p):
    roots,rows=p;fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    words=[(a,a+4*i,w) for a,ws in roots.items() for i,w in enumerate(ws)]
    return ('#pragma once\n#include "wii_ioctl_submit_prefix_v1403.h"\nnamespace v1404 {\n'
      'inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(words))+'> words{'+
      ','.join('undercover::wii::ReplyNativeWord{'+fmt(row)+'}' for row in words)+'};\n'
      'inline constexpr undercover::wii::IoctlSubmitPrefixExpectation expected{'+
      ','.join('undercover::wii::VectorEdge{'+fmt(row)+'}' for row in rows)+',words};\n}\n')
def install(root,p):
    roots,rows=p;sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    expected={a+4*i:(a,w) for a,ws in roots.items() for i,w in enumerate(ws)}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),expected)
    for site,dst in (WRAPPER,*CALLS):
        owners=[s for s in sources.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('submit prefix edges')
        verify_direct(owners[0],site,dst)
    for i,w in enumerate(roots[SUBMIT]):
        pc=SUBMIT+4*i;hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
        if sum(s.count(hook) for s in sources.values())!=1:raise ValueError('submit prior hook')
    done=set();changed={}
    for path,s in sources.items():
        old=s
        for i,w in enumerate(roots[QUEUE]):
            pc=QUEUE+4*i;s,found=hook_submit(s,pc,w)
            if not found:continue
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if pc in done or s.count(hook)!=1:raise ValueError('submit queue hook')
            done.add(pc);s=s.replace(hook,hook.replace('v1344_before','v1404_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('submit queue hook')
            changed[path]=s.replace(anchor,anchor+'\nvoid v1404_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if len(done)!=len(roots[QUEUE]):raise ValueError('submit queue coverage')
    for path,s in changed.items():path.write_text(s)
    print(f'V1404_PREFIX_TRANSLATION verified=1 labels={len(expected)} direct_edges=3 queue_labels={len(done)}')
def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=derive(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.out,p);return 0
        with (q.out/'v1404_private_ioctl_submit_prefix.h').open('x') as f:f.write(render(p))
        print(f'V1404_PREFIX_GEOMETRY verified=1 prefix_labels={len(p[0][SUBMIT])} queue_labels={len(p[0][QUEUE])}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','submit wrapper edge','submit queue shape','submit prefix edges','submit prior hook','submit queue hook','submit queue coverage',
            'completion hook label','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
            'helper direct native call','helper native return edge'}
        print('V1404_PREFIX_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
