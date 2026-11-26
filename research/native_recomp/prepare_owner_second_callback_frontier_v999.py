#!/usr/bin/env python3
"""Continue the second handler callback to its original wireless frontier."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_second_callback_time_v998 import plan as base_plan,header as base_header,install,patch_analyzer
from prepare_owner_callback_frontier_v820 import plan as frontier_plan
from prepare_v831_callback_frontier import render

def plan(dol,elf):
    p,shared,C,S,call,full,sites,prefix,time_header=base_plan(dol,elf)
    f,seen,stops,A,B=frontier_plan(dol,elf)
    q,T,D,U,R,ts,leaves=f
    fr,c,s,_,_,_=q
    roots,edges,indirect,iw,hw,dw,guard,extra=p[0]
    if (c,s)!=(C,S) or A in roots or B in roots or len(seen)!=27:raise ValueError('frontier geometry')
    if list(fr[C][:len(roots[C])-1])!=list(roots[C][:-1]):raise ValueError('frontier prefix')
    roots[C]=list(fr[C]);roots[A]=list(fr[A]);roots[B]=list(fr[B])
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    for a in (C,A,B):
        if any(b!=a and a<e and b<a+4*len(roots[a]) for b,e in spans):raise ValueError('frontier overlap')
    # These two exact original call instructions are observed, not
    # executed. Their independently authored synthetic guard bodies
    # are never admitted by the runtime witness.
    if roots[A]!=[0x4e800020] or roots[B]!=[0x4e800020]:raise ValueError('frontier guard')
    extra=(*extra[:-1],*((pc,dst,4,full[(pc-C)//4],roots[dst]) for pc,(_,dst) in sorted(stops.items())),extra[-1])
    q=(roots,edges,indirect,iw,hw,dw,guard,extra)
    expected={pc:(C,full[(pc-C)//4]) for pc in seen}
    return (q,*p[1:]),shared,C,S,call,full,sites,prefix,time_header,A,B,render(C,ts+4,expected,stops)

def header(p,shared,C,S,call,full,sites,prefix,time_header,A,B,frontier_header,out):
    base_header(p,shared,C,S,call,full,sites,prefix,time_header,out)
    with out.open('a') as f:
        f.write(f'\ninline constexpr uint32_t WirelessSetter=0x{A:08x}u,WirelessGetter=0x{B:08x}u;\n')
        f.write('inline constexpr std::array<uint32_t,1> wireless_refusal{0x4e800020u};\n')
        f.write(frontier_header.replace('#pragma once\n','',1))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p,shared,C,S,call,full,sites,prefix,th,A,B,fh=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,call,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:header(p,shared,C,S,call,full,sites,prefix,th,A,B,fh,x.output);print('V999_CALLBACK_FRONTIER_GEOMETRY original_indirect=1 labels=27 wireless_edges=2 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('frontier geometry','frontier prefix','frontier overlap','frontier guard','native coverage','native owner','hook identity')
        print('V999_CALLBACK_FRONTIER_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
