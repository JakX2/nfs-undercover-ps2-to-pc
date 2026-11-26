#!/usr/bin/env python3
"""Authenticate original cache helper and exact wrapper return traces."""
import argparse,struct
from pathlib import Path
from prepare_v1385_async_ioctl_geometry import plan,IOCTL,EDGES
from make_v639_open_geometry import geometry
from prepare_v419_full_start import MAX_DOL
from prepare_v625_ipc_client import audit_native,patch_return
from make_v626_ipc_fixture import backward_polls
from prepare_v680_si_helper import verify_direct
FLUSH=0x805222c0
CALLS=EDGES[2:4]
def derive(d,e):
    wrapper,*_=plan(d,e)
    _,_,roots=geometry(d,e)
    ws=roots[FLUSH]
    if len(ws)!=12 or ws[-2:]!=(0x44000002,0x4e800020):
        raise ValueError('flush geometry')
    resumes={site+4:wrapper[IOCTL][(site+4-IOCTL)//4] for site,_ in CALLS}
    polls=backward_polls({FLUSH:ws})
    if not polls or len(polls)>4:raise ValueError('flush polls')
    return ws,resumes,polls
def render(p):
    ws,resumes,polls=p
    fmt=lambda seq:','.join(f'0x{x:08x}u' for x in seq)
    return ('#pragma once\n#include "wii_ioctl_first_flush_v1398.h"\nnamespace v1398 {\n'
      'inline constexpr std::array<uint32_t,'+str(len(polls))+'> polls{'+fmt(polls)+'};\n'
      'inline constexpr undercover::wii::IoctlFirstFlushExpectation expected{'+fmt((ws[0],*resumes.values()))+',polls};\n}\n')
def install(root,p):
    ws,resumes,polls=p;sources={x:x.read_text() for x in sorted(root.glob('output_*.cpp'))}
    audit_native(sources.values(),(root/'main_output.cpp').read_text(),
        {**{FLUSH+4*i:(FLUSH,w) for i,w in enumerate(ws)},**{pc:(IOCTL,w) for pc,w in resumes.items()}})
    for site,dst in CALLS:
        owners=[s for s in sources.values() if f'loc_{site:X}: ;' in s]
        if len(owners)!=1:raise ValueError('flush edge')
        verify_direct(owners[0],site,dst)
    hits=dict.fromkeys(resumes,0);changed={}
    for path,s in sources.items():
        old=s
        for pc,w in resumes.items():
            if f'loc_{pc:X}: ;' in s:s=patch_return(s,w,pc);hits[pc]+=1
        if s!=old:changed[path]=s
    if any(n!=1 for n in hits.values()):raise ValueError('flush resume coverage')
    for path,s in changed.items():path.write_text(s)
    print(f'V1398_FLUSH_TRANSLATION verified=1 labels={len(ws)} return_edges=2 polls={len(polls)}')
def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--install',action='store_true');q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        p=derive(q.dol.read_bytes(),q.elf.read_bytes())
        if q.install:install(q.out,p);return 0
        with (q.out/'v1398_private_ioctl_flush.h').open('x') as f:f.write(render(p))
        print(f'V1398_FLUSH_GEOMETRY verified=1 labels={len(p[0])} polls={len(p[2])}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','flush geometry','flush polls','flush edge','flush resume coverage','native IPC return label',
                 'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper direct native call','helper native return edge'}
        print('V1398_FLUSH_PREP verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
