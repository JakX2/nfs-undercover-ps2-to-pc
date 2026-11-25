#!/usr/bin/env python3
"""Owner-only possible call graph after third handler call, no dynamic claims."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER,shape
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import edge,names,summarize
from audit_handler_suffix_v728 import target,restore_suffix
from si_nested_geometry_v693 import nested_plan
from classify_save_leaf_v683 import symbol_evidence
def walk(root,words,start):
    end=root+4*len(words)
    if root&3 or start&3 or not root<=start<end or not 1<=len(words)<=1024:raise ValueError('extent')
    _,direct,indirect=shape(root,words)
    calls={pc:(i+1,dst) for i,(pc,dst) in enumerate(sorted([*direct,*[(p,None) for p in indirect]]))}
    seen=set();todo=[start];edges={};returns=set();other=set()
    while todo:
        pc=todo.pop()
        if pc in seen:continue
        if pc&3 or not root<=pc<end:raise ValueError('fallthrough')
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        # Calls get an explicitly hypothetical fallthrough edge.
        if pc in calls:
            edges[pc]=calls[pc];todo.append(pc+4);continue
        if op in (16,18):
            dst=target(pc,w)
            if root<=dst<end and not w&1:todo.append(dst)
            else:other.add(pc)
            if op==18:continue
        elif op==19 and xo in (16,528):
            if xo==16 and not w&1:
                returns.add(pc)
                if ((w>>21)&20)!=20:todo.append(pc+4)
            else:other.add(pc)
            continue
        elif op==17 or op==19 and xo==50 or op==31 and xo==146:
            other.add(pc);continue
        todo.append(pc+4)
    return len(seen),len(returns),len(other),[edges[pc] for pc in sorted(edges)]
def inspect(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n);sizes=parse_functions(elf)
    site,third,_=edge(HANDLER,words,3)
    nested=nested_plan(dol,elf)[1]
    count,returns,other,edges=walk(HANDLER,words,site+4)
    print(f'V744_LATER_HANDLER verified=1 same_time_root={int(third==nested)} reachable={count} returns={returns} other={other} possible_calls={len(edges)} assumed_returns=1 execution=0')
    for ordinal,dst in edges:
        row=dict(ordinal=ordinal,kind=1 if dst is not None else 2,same_time=int(dst==third),exact=0,words=0,direct=0,indirect=0,tail=0,returns=0,mtmsr=0,system=0,restore_gprs=0)
        if dst is not None:
            size=sizes.get(dst,0)
            if 4<=size<=4096:
                row['exact']=1;code=exact(dol,elf,dst,size//4);s,_=summarize(dst,code)
                for k in ('words','direct','indirect','tail','returns','mtmsr','system'):row[k]=s[k]
            elif sum(a<dst<a+n for a,n in sizes.items())==1:
                for k in range(1,20):
                    code=exact(dol,elf,dst,k)
                    if code[-1]==0x4e800020:
                        row['restore_gprs']=restore_suffix(code);break
        print('V744_LATER_EDGE '+' '.join(f'{k}={v}' for k,v in row.items())+' name='+(names(elf,dst) if dst is not None else 'indirect'))
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError):
        print('V744_LATER_HANDLER verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
