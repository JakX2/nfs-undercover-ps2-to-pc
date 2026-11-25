#!/usr/bin/env python3
"""Authenticate a focused callback through its original system-time return."""
import argparse
import struct
from pathlib import Path
from prepare_owner_callback_prefix_v797 import plan as prefix_plan, install as prefix_install
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_owner_pair_v753 import H, BLR
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact
from audit_callback_frontiers_v799 import call_sites, continuations
from audit_os_leaf_v703 import plan as leaf_plan
from si_nested_geometry_v693 import nested_plan
from audit_handler_third_v740 import summarize
from prepare_owner_scheduler_v722 import reachable


def extend(root, words, time):
    sites = call_sites(root, words)
    if len(sites) < 2 or sites[1][1:] != (1, time):
        raise ValueError('time edge')
    first, second = sites[0][0], sites[1][0]
    rows = continuations(root, words)
    if rows[1][4] != (2,) or rows[1][2] or any(rows[1][5]):
        raise ValueError('time frontier')
    idx = (second-root)//4
    if idx+1 >= len(words) or idx>64 or second<=first:
        raise ValueError('time extent')
    w = words[idx+1]
    if w>>26 in (16,17,18,19) or w>>26==31 and (w>>1)&1023==146:
        raise ValueError('return instruction')
    code = list(words[:idx+2])+[BLR]
    # All original prefix paths must stay inside the bounded fragment.
    if any(pc<root or pc>=root+4*len(code) for pc in reachable(root,code)):
        raise ValueError('time reachability')
    return second, code


def plan(dol, elf):
    roots,C,S,site,sb,disp = prefix_plan(dol,elf)
    _,T,_,_,tw = nested_plan(dol,elf)
    summary,_ = summarize(T,tw)
    if len(tw)!=25 or summary['direct']!=3 or any(summary[k] for k in ('conditional','backward','indirect','tail','mtmsr','system')) or tw[-1]!=BLR:
        raise ValueError('time shape')
    ts,code=extend(C,exact(dol,elf,C,172),T)
    leaves=leaf_plan(dol,elf)
    D,U,R=[x[1] for x in leaves]
    roots[C]=code;roots[T]=tw
    for x in leaves:roots[x[1]]=x[5]
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=7 or any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):
        raise ValueError('root overlap')
    return (roots,C,S,site,sb,disp),T,D,U,R,ts,leaves


def header(p,out):
    (roots,C,S,site,sb,disp),T,D,U,R,ts,leaves=p
    s='#pragma once\n#include <array>\n#include <cstdint>\n'
    vals={'H':H,'C':C,'S':S,'SaveCall':site,'Resume':site+4,'T':T,'D':D,'U':U,'R':R,'TimeCall':ts,'TimeResume':ts+4}
    s+='inline constexpr uint32_t '+','.join(f'{k}=0x{v:08x}u' for k,v in vals.items())+';\n'
    s+=f'inline constexpr unsigned SaveBase={sb};\ninline constexpr int32_t SaveDisp={disp};\n'
    for name,addr in zip(('caller_words','prefix_words','save_words','system_words','disable_words','time_words','restore_words'),(H,C,S,T,D,U,R)):
        ws=roots[addr];s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+','.join(f'0x{w:08x}u' for w in ws)+'};\n'
    for name,idx in (('leaf_sites',0),('leaf_branches',3)):
        s+=f'inline constexpr std::array<uint32_t,3> {name}{{'+','.join(f'0x{x[idx]:08x}u' for x in leaves)+'};\n'
    with out.open('x') as f:f.write(s)


def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true')
    x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p=plan(x.dol.read_bytes(),x.elf.read_bytes())
        q,T,D,U,R,ts,leaves=p
        if x.install:prefix_install(q,x.output,[(q[1],ts,T),*[(T,l[0],l[1]) for l in leaves]],True)
        elif x.patch_analyzer:patch_analyzer(q,x.output)
        else:
            header(p,x.output)
            print('V802_CALLBACK_GEOMETRY verified=1 roots=6 original_time=1 leaf_roots=3 callback_return=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        allow=('time edge','time frontier','time extent','return instruction','time reachability','time shape','root overlap','native coverage','native owner','hook identity','hook coverage')
        print('V802_CALLBACK_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allow else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
