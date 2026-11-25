#!/usr/bin/env python3
"""Stage original post-setter callback control without executing either callee."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact
from prepare_owner_callback_write_v838 import plan as joined_plan,header as joined_header
from prepare_owner_wireless_return_v837 import install,patch_analyzer,validate_overlaps
from prepare_owner_pair_v753 import alias,pair_shape
from audit_callback_frontiers_v799 import call_sites,continuations
from audit_handler_suffix_v728 import target
from make_private_elf_symbol_map import parse_functions
from prepare_owner_scheduler_v722 import reachable
BLR=0x4e800020

def plan(dol,elf):
    q,merged=joined_plan(dol,elf)
    base,restore,aliases,revision,immex,unlock,shared=merged
    roots,A,B,W,L,guards=base
    C=q[0][0][1];S=q[0][0][2]
    original=exact(dol,elf,C,172);sites=call_sites(C,original)
    if continuations(C,original)[3][1:]!=(21,1,1,(4,13),(0,0,0,0)):
        raise ValueError('postsetter census')
    resume=sites[2][0]+4
    calls={pc:(i,k,dst) for i,(pc,k,dst) in enumerate(sites,1)}
    seen=set();todo=[resume];stops={}
    while todo:
        pc=todo.pop()
        if pc in seen:continue
        if pc&3 or not C<=pc<C+688 or len(seen)>=64:raise ValueError('postsetter extent')
        seen.add(pc);w=original[(pc-C)//4];op=w>>26;xo=(w>>1)&1023
        if pc in calls:
            i,k,dst=calls[pc]
            if (i,k) not in ((4,2),(13,1)):raise ValueError('postsetter call')
            stops[pc]=(i,k,dst);continue
        if op in (16,18):
            if w&3:raise ValueError('postsetter control')
            todo.append(target(pc,w))
            if op==18:continue
        elif op==17 or (op==19 and xo in (16,50,528)) or (op==31 and xo==146):
            raise ValueError('postsetter control')
        todo.append(pc+4)
    if len(seen)!=21 or sorted(i for i,k,dst in stops.values())!=[4,13]:
        raise ValueError('postsetter shape')
    R=sites[12][2]
    sizes=parse_functions(elf);save=roots[S]
    restore_code=alias(dol,elf,R,sizes,len(save)-1)
    pair_shape(list(save),restore_code,len(save)-1)
    if R in roots and list(roots[R])!=restore_code:raise ValueError('postsetter restore')
    roots[R]=restore_code;aliases=set(aliases)|{R}
    old=list(roots[C]);end=max(C+4*len(old),max(seen)+8)
    if end>C+688:raise ValueError('postsetter extent')
    old.extend([BLR]*((end-C)//4-len(old)))
    for pc in seen:
        i=(pc-C)//4
        if old[i] not in (BLR,original[i]):raise ValueError('postsetter identity')
        old[i]=original[i]
    roots[C]=old
    if not seen.issubset(reachable(C,old)):raise ValueError('postsetter coverage')
    shared=validate_overlaps(roots,aliases)
    merged=(base,restore,aliases,revision,immex,unlock,shared)
    return (q,merged),C,resume,sorted(seen),stops

def header(p,out):
    joined,C,resume,seen,stops=p
    joined_header(joined,out)
    roots=joined[1][0][0]
    with out.open('a') as f:
        f.write(f'inline constexpr uint32_t PostSetterResume=0x{resume:08x}u;\n')
        f.write(f'inline constexpr std::array<std::array<uint32_t,2>,{len(seen)}> postsetter_words{{{{'+
            ','.join(f'{{0x{pc:08x}u,0x{roots[C][(pc-C)//4]:08x}u}}' for pc in seen)+'}};\n')
        f.write('inline constexpr std::array<std::array<uint32_t,3>,2> postsetter_edges{{'+
            ','.join(f'{{0x{pc:08x}u,0x{(dst or 0):08x}u,{i}u}}' for pc,(i,k,dst) in sorted(stops.items()))+'}};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());joined,C,resume,seen,stops=q
        if a.install:
            install(joined[1],a.output,[(C,pc) for pc,(_,k,_) in stops.items() if k==2])
            print('V842_POST_SETTER_NATIVE_ROUTE verified=1 labels=21 indirect=1 restore=1 execution=0')
        elif a.patch_analyzer:patch_analyzer(joined[1],a.output)
        else:
            header(q,a.output);print('V842_POST_SETTER_GEOMETRY verified=1 labels=21 backward=1 store=1 indirect=1 restore=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('postsetter census','postsetter extent','postsetter call','postsetter control','postsetter shape','postsetter restore','postsetter identity','postsetter coverage','shared suffix identity','indirect coverage','native edge','native owner','native coverage','hook identity','indirect label','indirect LR','indirect dispatch','indirect fallback','alias root','alias symbol','pair shape','frame offset')
        print('V842_POST_SETTER_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
