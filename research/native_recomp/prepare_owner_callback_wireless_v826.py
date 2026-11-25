#!/usr/bin/env python3
"""Join the original callback frontier to the verified wireless wrappers.

The synthetic initial SRAM ID is explicit. Complete original setter/getter
and UnlockSram execute, while the unimplemented EXI lane is a refusal.
"""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact
from prepare_owner_callback_frontier_v820 import plan as frontier_plan,header as frontier_header
from prepare_owner_wireless_v816 import plan as wireless_plan,install as install_wireless,H,J
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_owner_scheduler_v722 import reachable
from audit_callback_frontiers_v799 import call_sites
from audit_handler_suffix_v728 import target
BLR=0x4e800020

def plan(dol,elf):
    p=frontier_plan(dol,elf);q,seen,stops,A,B=p
    base,T,D,TimeLeaf,R,ts,leaves=q;roots,C,S,site,sb,disp=base
    wr,WA,WB,W,L,guards=wireless_plan(dol,elf)
    if (WA,WB)!=(A,B):raise ValueError('wrapper identity')
    original=exact(dol,elf,C,172)
    # Authentic successor label after each possible first call; no
    # original successor is allowed to execute in this test.
    words=list(roots[C]);limit=C+4*len(original)
    for pc in stops:
        nxt=pc+4
        while len(words)<(nxt-C)//4+2:words.append(BLR)
        w=original[(nxt-C)//4]
        if w>>26 in (17,18,19) and (w>>26!=18 or w&3):
            raise ValueError('wireless successor shape')
        words[(nxt-C)//4]=w
        if w>>26 in (16,18):
            dst=target(nxt,w)
            if not C<=dst<limit or w&3:raise ValueError('wireless successor branch')
            while len(words)<(dst-C)//4+1:words.append(BLR)
    roots[C]=words
    for a,ws in wr.items():
        if a in (H,J):continue
        if a in (A,B):roots[a]=ws
        elif a in roots:
            if list(roots[a])!=list(ws):raise ValueError('shared root')
        else:roots[a]=ws
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(y>x for (_,y),(x,_) in zip(spans,spans[1:])):raise ValueError('root overlap')
    return p,W,L,guards

def header(p,out):
    q,W,L,guards=p
    frontier_header(q,out)
    roots=q[0][0][0]
    fmt=lambda xs:','.join(f'0x{v:08x}u' for v in xs)
    with out.open('a') as f:
        f.write('#include <span>\n')
        f.write(f'inline constexpr uint32_t Unlock=0x{W:08x}u,LockGuard=0x{L:08x}u;\n')
        f.write(f'inline constexpr std::array<uint32_t,{len(guards)}> exi_guards{{'+fmt(guards)+'};\n')
        for i,(a,ws) in enumerate(roots.items()):
            f.write(f'inline constexpr std::array<uint32_t,{len(ws)}> all_words_{i}{{'+fmt(ws)+'};\n')
        f.write('struct Root{uint32_t address;std::span<const uint32_t> words;};\n')
        f.write(f'inline constexpr std::array<Root,{len(roots)}> all_roots{{{{'+','.join(
            f'Root{{0x{a:08x}u,all_words_{i}}}' for i,a in enumerate(roots))+'}};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(a.dol.read_bytes(),a.elf.read_bytes());q,W,L,guards=p
        base=q[0][0];roots=base[0]
        if a.install:
            install_wireless((roots,q[3],q[4],W,L,guards),a.output)
            print('V826_JOIN_NATIVE_ROUTE verified=1 time=1 wireless=1 exi_guard=1 execution=0')
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            header(p,a.output);print('V826_JOIN_GEOMETRY verified=1 time=1 wireless=1 exi_guard=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('wrapper identity','wireless successor shape','wireless successor branch','shared root','root overlap','native coverage','native owner','native edge','hook identity','hook include','hook coverage')
        print('V826_JOIN_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
