#!/usr/bin/env python3
"""Private native third allocation audit, hooks, and read-only expectation."""
import argparse,struct
from pathlib import Path
from prepare_v1385_async_ioctl_geometry import plan,IOCTL,EDGES
from make_v639_open_geometry import geometry,PROFILE,ALLOC
from apply_open_roots_v645 import irq_spans
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_v624_ipc_geometry import exact_words
from prepare_owner_scheduler_v722 import reachable
from derive_allocator_census_v1345 import census
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v1337_open_completion import hook_submit
from make_start_to_ios_open_v71 import EDGES as OPEN_EDGES
RESUME=EDGES[1][0]+4
DISABLE,RESTORE=0x805265ac,0x805265d4
CALLS=((0x8051ab60,DISABLE),(0x8051ad10,RESTORE))

def derive(d,e):
    wrapper,*_=plan(d,e)
    _,_,roots=geometry(d,e)
    roots={a:roots[a] for a in (PROFILE,ALLOC)}
    roots.update({a:exact_words(d,e,a,n//4) for a,n in irq_spans(d,e)})
    n,ret,stores=census(ALLOC,roots[ALLOC],CALLS)
    if ret!=1 or not stores or len(roots[PROFILE])!=1 or EDGES[1][1]!=PROFILE:
        raise ValueError('allocation geometry')
    rows=tuple((dst,site+4,roots[ALLOC][(site-ALLOC)//4],roots[dst][0]) for site,dst in CALLS)
    if any(direct_bl(w,lr-4)!=dst for dst,lr,w,_ in rows):raise ValueError('allocation edge')
    return roots,rows,wrapper[IOCTL][(RESUME-IOCTL)//4],n,sum(stores.values())

def render(p):
    roots,edges,resume,_,_=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    words=[(a,pc,ws[(pc-a)//4]) for a,ws in roots.items() for pc in sorted(reachable(a,ws))]
    return ('#pragma once\n#include "wii_ioctl_allocation_v1387.h"\nnamespace v1387 {\n'
      'inline constexpr std::array<undercover::wii::ReplyNativeWord,'+str(len(words))+'> words{'+
      ','.join('undercover::wii::ReplyNativeWord{'+fmt(row)+'}' for row in words)+'};\n'
      'inline constexpr undercover::wii::IoctlAllocationExpectation expected{'+fmt((PROFILE,ALLOC,RESUME,resume))+','+
      ','.join('undercover::wii::VectorEdge{'+fmt(row)+'}' for row in edges)+',words};\n}\n')

def install(root,p):
    roots,edges,resume,n,stores=p
    sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    expected={pc:(a,ws[(pc-a)//4]) for a,ws in roots.items() for pc in reachable(a,ws)}
    expected[RESUME]=(IOCTL,resume)
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),expected)
    for site,dst in CALLS:
        owners=[s for s in sources.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('allocation edge')
        verify_direct(owners[0],site,dst)
    for pc,(a,w) in expected.items():
        if a in (DISABLE,RESTORE):
            hook=f'    v1270_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if sum(s.count(hook) for s in sources.values())!=1:raise ValueError('allocation shared hook')
    wanted={pc:w for pc,(a,w) in expected.items() if a not in (DISABLE,RESTORE)}
    done=set();changed={}
    for path,s in sources.items():
        old=s
        for pc,w in wanted.items():
            s,found=hook_submit(s,pc,w)
            if not found:continue
            if pc in done:raise ValueError('allocation hook')
            done.add(pc)
            hook=f'    v1344_before(ctx,0x{pc:08x}u,0x{w:08x}u);'
            if s.count(hook)!=1:raise ValueError('allocation hook')
            s=s.replace(hook,hook.replace('v1344_before','v1387_before'))
        if s!=old:
            anchor='#include "runtime/cpu_context.h"'
            if s.count(anchor)!=1:raise ValueError('allocation hook')
            changed[path]=s.replace(anchor,anchor+'\nvoid v1387_before(nwii::runtime::CPUContext&,uint32_t,uint32_t);')
    if done!=set(wanted):raise ValueError('allocation hook coverage')
    for path,s in changed.items():path.write_text(s)
    print(f'V1387_ALLOCATION_TRANSLATION verified=1 labels={len(expected)} body_labels={n} static_stores={stores} direct_edges=2')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=derive(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.out,p);return 0
        with (q.out/'v1387_private_ioctl_allocation.h').open('x') as f:f.write(render(p))
        print(f'V1387_ALLOCATION_GEOMETRY verified=1 body_labels={p[3]} static_stores={p[4]}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','allocation geometry','allocation edge','allocation shared hook','allocation hook','allocation hook coverage',
            'allocator unsupported store','allocator extent','allocator call','allocator control','allocator coverage',
            'reachable fallthrough','reachable external conditional','completion hook label','native IPC duplicate root',
            'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch',
            'helper direct native call','helper native return edge'}
        print('V1387_ALLOCATION_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
