#!/usr/bin/env python3
"""Authenticate the original third handler call and three already-known OS leaves."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import HANDLER,DISABLE,TIME,RESTORE,exact
from prepare_owner_second_ack_v955 import plan as old_plan,bounded,install
from prepare_owner_second_dispatch_v946 import patch_analyzer,header as dispatch_header
from prepare_v742_handler_time import plan as time_plan
from audit_os_leaf_v703 import plan as leaf_plan
from prepare_v672_si_ack_route import call_census

def plan(dol,elf):
    roots,edges,indirect,iw,hw,dw,guard,extra=old_plan(dol,elf)
    site,nested,end,word=time_plan(dol,elf)
    if nested!=extra[2][1] or end!=nested+4*len(roots[nested]):raise ValueError('time root')
    leaves=leaf_plan(dol,elf)
    if [r[1] for r in leaves]!=[DISABLE,TIME,RESTORE]:raise ValueError('leaf order')
    # Only new authorized call sites are restored. No new root is introduced.
    new_extra=(*extra,(site,nested,end-nested,word,exact(dol,elf,nested,len(roots[nested]))),
        *((s,t,e-t,w,code) for s,t,e,w,_,code,_ in leaves))
    allowed={(s,t) for s,t,_,_,_ in new_extra}
    for a in (HANDLER,nested):
        raw=exact(dol,elf,a,len(roots[a]))
        guard.difference_update(range(a,a+4*len(raw),4))
        roots[a],g=bounded(a,raw,allowed);guard.update(g)
    msr=[]
    for _,root,_,_,_,code,mt in leaves:
        if list(code)!=roots[root]:raise ValueError('leaf words')
        for i in mt:msr.append((root+4*i,code[i]))
    if len(msr)!=2 or len(allowed)!=7:raise ValueError('leaf geometry')
    census=call_census(HANDLER,exact(dol,elf,HANDLER,len(roots[HANDLER])))
    frontier=[(pc,ordinal,kind) for pc,(ordinal,kind) in sorted(census.items()) if pc in guard and ordinal>=4]
    if not frontier or any(kind not in (1,2) or ordinal>32 for _,ordinal,kind in frontier):raise ValueError('frontier census')
    return (roots,edges,indirect,iw,hw,dw,guard,new_extra),site,msr,frontier

def header(q,out,site,msr,frontier):
    roots,edges,indirect,iw,hw,dw,guard,extra=q
    dispatch_header(q[:7],out)
    fmt=lambda v:','.join(f'0x{x:08x}u' for x in v)
    with out.open('a') as f:
        for name,(_,dst,_,_,_) in zip(('Save','Completion','Nested'),extra):
            ws=roots[dst]
            f.write(f'inline constexpr uint32_t {name}=0x{dst:08x}u;\n')
            f.write(f'inline constexpr std::array<uint32_t,{len(ws)}> {name.lower()}_words{{'+fmt(ws)+'};\n')
        f.write('inline constexpr std::array<std::array<uint32_t,2>,7> AckEdges{{'+','.join('std::array<uint32_t,2>{'+fmt((s,d))+'}' for s,d,_,_,_ in extra)+'}};\n')
        f.write(f'inline constexpr uint32_t TimeCall=0x{site:08x}u;\n')
        f.write(f'inline constexpr std::array<std::array<uint32_t,3>,{len(frontier)}> HandlerFrontier{{{{'+','.join('std::array<uint32_t,3>{'+fmt(r)+'}' for r in frontier)+'}};\n')
        f.write('inline constexpr std::array<undercover::wii::AckMsrSite,2> AckMsr{{'+','.join('{'+fmt(r)+'}' for r in msr)+'}};\n')
    s=out.read_text();out.write_text(s.replace('#include "wii_si_dispatch_v667.h"','#include "wii_si_dispatch_v667.h"\n#include "wii_bounded_ack_call_route_v956.h"'))

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q,site,msr,frontier=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q[:7],a.output)
        else:header(q,a.output,site,msr,frontier);print('V966_TIME_GEOMETRY roots=9 handler_edges=7 msr_sites=2 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('time root','leaf order','leaf words','leaf geometry','frontier census','native coverage','native owner','hook identity','hook include','hook coverage','reachability','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V966_TIME_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
