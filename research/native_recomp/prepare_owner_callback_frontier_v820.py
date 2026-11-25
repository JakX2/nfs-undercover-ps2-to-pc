#!/usr/bin/env python3
"""Continue genuine callback time return to the first original wireless call.

Only original reachable prefix/frontier words are privately staged.
Unreachable padding and guarded call targets are independent BLR words.
The test must stop before the first new linked call executes.
"""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact
from prepare_owner_callback_time_v802 import plan as time_plan,header as time_header
from prepare_owner_callback_prefix_v797 import install as prefix_install
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_owner_scheduler_v722 import reachable
from audit_callback_frontiers_v799 import call_sites,continuations
from audit_callback_posttime_v812 import first_roots,SDK
from audit_handler_third_v740 import names
from audit_handler_suffix_v728 import target
BLR=0x4e800020

def frontier(root,words,start):
    sites={pc:(i,k,dst) for i,(pc,k,dst) in enumerate(call_sites(root,words),1)}
    seen=set();work=[start];stops={}
    while work:
        pc=work.pop()
        if pc in seen:continue
        if pc&3 or not root<=pc<root+4*len(words) or len(seen)>=64:raise ValueError('frontier extent')
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if pc in sites:
            ordinal,kind,dst=sites[pc]
            if ordinal not in (3,5) or kind!=1:raise ValueError('frontier call')
            stops[pc]=(ordinal,dst);continue
        if op in (16,18):
            dst=target(pc,w)
            if w&3 or dst<=pc or dst<start:raise ValueError('frontier branch')
            work.append(dst)
            if op==18:continue
        elif op==17 or (op==19 and xo in (16,50,528)) or (op==31 and xo==146):
            raise ValueError('frontier control')
        work.append(pc+4)
    if len(seen)!=27 or sorted(o for o,_ in stops.values())!=[3,5]:
        raise ValueError('frontier shape')
    return seen,stops

def plan(dol,elf):
    p=time_plan(dol,elf);q,T,D,U,R,ts,leaves=p;roots,C,S,site,sb,disp=q
    original=exact(dol,elf,C,172)
    rows=continuations(C,original)
    if rows[2][1:]!=(27,0,3,(3,5),(0,0,0,0)):raise ValueError('frontier shape')
    seen,stops=frontier(C,original,ts+4)
    A,B=first_roots(C,original)
    if [names(elf,x,SDK) for x in (A,B)]!=['OSSetWirelessID','OSGetWirelessID']:
        raise ValueError('wireless identity')
    old=roots[C]
    # Preserve all original time-prefix words, including its stop label.
    prefix={C+4*i for i in range(len(old)-1)}
    exact_pcs=prefix|seen
    end=max(exact_pcs)+8
    words=[original[(a-C)//4] if a in exact_pcs else BLR for a in range(C,end,4)]
    roots[C]=words
    if A in roots or B in roots:raise ValueError('guard overlap')
    roots[A]=[BLR];roots[B]=[BLR]
    rs=reachable(C,words)
    if not exact_pcs.issubset(rs) or any(a not in exact_pcs and words[(a-C)//4]!=BLR for a in rs):
        raise ValueError('frontier coverage')
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=9 or any(y>x for (_,y),(x,_) in zip(spans,spans[1:])):
        raise ValueError('root overlap')
    return p,sorted(seen),stops,A,B

def header(p,out):
    q,seen,stops,A,B=p
    time_header(q,out)
    fmt=lambda xs:','.join(f'0x{v:08x}u' for v in xs)
    with out.open('a') as f:
        f.write(f'inline constexpr std::array<uint32_t,{len(seen)}> frontier_sites{{'+fmt(seen)+'};\n')
        f.write('inline constexpr std::array<uint32_t,2> wireless_sites{'+fmt(sorted(stops))+'};\n')
        f.write('inline constexpr std::array<uint32_t,2> wireless_roots{'+fmt([stops[a][1] for a in sorted(stops)])+'};\n')
        f.write('inline constexpr std::array<uint32_t,2> wireless_ordinals{'+fmt([stops[a][0] for a in sorted(stops)])+'};\n')
        f.write(f'inline constexpr uint32_t Setter=0x{A:08x}u,Getter=0x{B:08x}u;\n')
        f.write('inline constexpr std::array<uint32_t,1> refusal_words{0x4e800020u};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(a.dol.read_bytes(),a.elf.read_bytes());q,seen,stops,A,B=p
        base,T,D,U,R,ts,leaves=q
        if a.install:
            prefix_install(base,a.output,[(base[1],ts,T),*[(T,l[0],l[1]) for l in leaves],*[(base[1],pc,dst) for pc,(_,dst) in sorted(stops.items())]],True)
            print('V820_FRONTIER_NATIVE_ROUTE verified=1 labels=27 wireless_edges=2 execution=0')
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            header(p,a.output);print('V820_FRONTIER_GEOMETRY verified=1 labels=27 wireless_edges=2')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('frontier extent','frontier call','frontier branch','frontier control','frontier shape','wireless identity','guard overlap','frontier coverage','root overlap','native coverage','native owner','hook identity','hook coverage')
        print('V820_FRONTIER_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
