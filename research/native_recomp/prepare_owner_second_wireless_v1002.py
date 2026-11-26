#!/usr/bin/env python3
"""Join second-handler wireless wrappers without fabricating EXI writes."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_second_callback_frontier_v999 import plan as base_plan,header as base_header,install,patch_analyzer
from prepare_owner_callback_wireless_v826 import plan as wrapper_plan
from prepare_owner_pair_v753 import H
from prepare_v667_si_dispatch import DISABLE,RESTORE
from audit_callback_frontiers_v799 import call_sites

def plan(dol,elf):
    p,shared,C,S,call,full,sites,prefix,th,A,B,fh=base_plan(dol,elf)
    q,U,L,guards=wrapper_plan(dol,elf)
    base,T,D,TL,R,ts,leaves=q[0]
    wr,c,s,_,_,_=base
    roots,edges,indirect,iw,hw,dw,guard,extra=p[0]
    if (c,s,q[3],q[4],D,R)!=(C,S,A,B,DISABLE,RESTORE):raise ValueError('wrapper geometry')
    if roots[A]!=[0x4e800020] or roots[B]!=[0x4e800020] or len(guards)!=7:raise ValueError('wrapper guards')
    for pc in q[1]:
        if roots[C][(pc-C)//4]!=wr[C][(pc-C)//4]:raise ValueError('wrapper frontier')
    roots[C]=list(wr[C]);added=[]
    for a,ws in wr.items():
        if a in (H,C):continue
        if a in (A,B) or a not in roots:
            roots[a]=list(ws);added.append(a)
        elif list(roots[a])!=list(ws):raise ValueError('wrapper shared')
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    for a in (*added,C):
        if any(b!=a and a<end and b<a+4*len(roots[a]) for b,end in spans):raise ValueError('wrapper overlap')
    if set(added)!={A,B,U,*guards} or any(roots[a]!=[0x4e800020] for a in guards):raise ValueError('wrapper guards')
    new=[]
    for a in (A,B,U):
        for pc,kind,dst in call_sites(a,roots[a]):
            if kind!=1 or dst not in roots:raise ValueError('wrapper edge')
            new.append((pc,dst,4*len(roots[dst]),roots[a][(pc-a)//4],roots[dst]))
    extra=(*extra[:-1],*new,extra[-1])
    return ( (roots,edges,indirect,iw,hw,dw,guard,extra),*p[1:]),shared,C,S,call,full,sites,prefix,th,A,B,fh,U,L,added,q[2],guards

def header(p,shared,C,S,call,full,sites,prefix,th,A,B,fh,U,L,added,stops,guards,out):
    base_header(p,shared,C,S,call,full,sites,prefix,th,A,B,fh,out)
    roots=p[0][0];fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    with out.open('a') as f:
        f.write('\n#include "wii_wireless_wrapper_v844.h"\n')
        f.write(f'inline constexpr uint32_t WirelessLock=0x{L:08x}u,WirelessSram=0x806f52c0u;\n')
        for i,a in enumerate(added):
            f.write(f'inline constexpr std::array<uint32_t,{len(roots[a])}> wireless_words_{i}{{'+fmt(roots[a])+'};\n')
        f.write(f'inline constexpr std::array<undercover::wii::WirelessCode,{len(added)}> wireless_roots{{{{'+','.join(f'undercover::wii::WirelessCode{{0x{a:08x}u,wireless_words_{i}}}' for i,a in enumerate(added))+'}};\n')
        f.write(f'inline constexpr std::array<uint32_t,{len(guards)}> WirelessGuards{{'+fmt(guards)+'};\n')
        code=[f'wireless_roots[{added.index(a)}]' for a in (A,B,U)]+['undercover::wii::WirelessCode{Disable,disable_words}','undercover::wii::WirelessCode{Restore,restore_words}']
        erows=[f'undercover::wii::WirelessEdge{{{fmt((pc,full[(pc-C)//4],full[(pc-C)//4+1]))},{ordinal}u}}' for pc,(ordinal,_) in sorted(stops.items())]
        f.write('inline constexpr undercover::wii::WirelessExpectation WirelessExpected{{'+','.join(code)+'},{'+','.join(erows)+'},WirelessLock,0x4e800020u,WirelessSram};\n')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        result=plan(x.dol.read_bytes(),x.elf.read_bytes());p,_,_,_,call,*_=result
        if x.install:install(p,call,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:header(*result,x.output);print('V1002_WRAPPER_GEOMETRY original_wrappers=2 unlock=1 exi_guards=7 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('wrapper geometry','wrapper guards','wrapper frontier','wrapper shared','wrapper overlap','wrapper edge','native coverage','native owner','hook identity')
        print('V1002_WRAPPER_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
