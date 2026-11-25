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
from prepare_owner_wireless_v816 import H,J
from prepare_owner_wireless_return_v837 import plan as complete_plan,install as install_complete,patch_analyzer as patch_complete,validate_overlaps
from prepare_owner_pair_v753 import alias
from make_private_elf_symbol_map import parse_functions
from make_start_to_exi_transaction_v56 import IMM,SYNC,SELECT,DESELECT,HWREV,IRQMASK
from prepare_owner_scheduler_v722 import reachable
from audit_callback_frontiers_v799 import call_sites
from audit_handler_suffix_v728 import target
BLR=0x4e800020

def plan(dol,elf):
    p=frontier_plan(dol,elf);q,seen,stops,A,B=p
    base,T,D,TimeLeaf,R,ts,leaves=q;roots,C,S,site,sb,disp=base
    complete=complete_plan(dol,elf)
    (wr,WA,WB,W,L,guards),restore,aliases,revision,immex,unlock,shared=complete
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
    # Callback save alias can share a suffix with the verified EXI aliases.
    aliases=set(aliases)|{S}
    shared=validate_overlaps(roots,aliases)
    merged=((roots,A,B,W,L,guards),restore,aliases,revision,immex,unlock,shared)
    return p,merged

def header(p,out):
    q,merged=p
    (roots,A,B,W,L,guards),restore,aliases,revision,immex,unlock,shared=merged
    frontier_header(q,out)
    roots=q[0][0][0]
    fmt=lambda xs:','.join(f'0x{v:08x}u' for v in xs)
    with out.open('a') as f:
        f.write('#include <span>\n')
        f.write('namespace write_roots {\n')
        vals={'U':W,'L':L,'Imm':IMM,'Sync':SYNC,'ImmEx':immex,'Select':SELECT,'Deselect':DESELECT,'ExiUnlock':unlock,'Revision':HWREV,'RevisionRead':revision,'MaskHelper':IRQMASK}
        f.write('inline constexpr uint32_t '+','.join(f'{k}=0x{v:08x}u' for k,v in vals.items())+';\n')
        f.write('struct RestoreRule{uint32_t root;unsigned count,base;int32_t disp;};\n')
        unique={row[0]:row for row in restore}
        f.write(f'inline constexpr std::array<RestoreRule,{len(unique)}> restore_rules{{{{'+','.join(f'RestoreRule{{0x{a:08x}u,{n}u,{b}u,{disp}}}' for a,n,b,disp in unique.values())+'}};\n}\n')
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
        p=plan(a.dol.read_bytes(),a.elf.read_bytes());q,merged=p
        if a.install:
            install_complete(merged,a.output)
            print('V838_JOIN_NATIVE_ROUTE verified=1 time=1 wireless=1 complete_write=1 execution=0')
        elif a.patch_analyzer:patch_complete(merged,a.output)
        else:
            header(p,a.output);print(f'V838_JOIN_GEOMETRY verified=1 time=1 wireless=1 shared_suffixes={merged[-1]}')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('shared suffix identity','wrapper identity','wireless successor shape','wireless successor branch','shared root','root overlap','native coverage','native owner','native edge','hook identity','hook include','hook coverage')
        print('V838_JOIN_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
