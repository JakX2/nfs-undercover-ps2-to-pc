#!/usr/bin/env python3
"""Private bounded dependency graph for likely subsequent SI handler calls."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE,TIME,SCHED
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import edge,names,summarize
from audit_si_deep_v695 import census,call_kind
from audit_handler_suffix_v728 import target,restore_suffix
from si_nested_geometry_v693 import nested_plan
from si_second_geometry_v688 import second_plan
def graph(root,code):
    if root&3 or not 1<=len(code)<=1024:raise ValueError('extent')
    out=[]
    for i,w in enumerate(code):
        pc=root+4*i;kind=call_kind(w)
        if kind:
            out.append((kind,target(pc,w) if kind==1 else None))
        elif w>>26 in (16,18):
            dst=target(pc,w)
            if not root<=dst<root+4*len(code):out.append((3,dst))
    return out
def leaf_alias(dol,elf,dst,sizes):
    if sum(a<dst<a+n for a,n in sizes.items())!=1:return 0
    for n in range(1,20):
        try:code=exact(dol,elf,dst,n)
        except ValueError:return 0
        if code[-1]==0x4e800020:return restore_suffix(code)
    return 0
def inspect(dol,elf):
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n);sizes=parse_functions(elf)
    known={DISABLE:'disable',RESTORE:'restore',TIME:'timebase',SCHED:'scheduler',
           nested_plan(dol,elf)[1]:'system_time',second_plan(dol,elf)[1]:'second'}
    roots={i:edge(HANDLER,handler,i)[1] for i in (4,5,7,8)}
    for i,a in roots.items():known[a]='handler_'+str(i)
    for lane,root in roots.items():
        size=sizes.get(root,0)
        if not 4<=size<=4096:raise ValueError('root extent')
        code=exact(dol,elf,root,size//4)
        summary,_=summarize(root,code);counts,first=census(root,code)
        print(f'V749_ROOT lane={lane} name={names(elf,root)} '+' '.join(f'{k}={v}' for k,v in summary.items()))
        print(f'V749_PREFIX lane={lane} first_calls={len(first)} '+' '.join(f'{k}={v}' for k,v in counts.items()))
        ordinal=0
        for kind,dst in graph(root,code):
            if kind!=3:ordinal+=1
            row=dict(lane=lane,ordinal=ordinal if kind!=3 else 0,kind=kind,first=int(kind!=3 and ordinal in first),known=known.get(dst,'other'),exact=0,words=0,direct=0,indirect=0,tail=0,returns=0,mtmsr=0,system=0,restore_gprs=0)
            if dst is not None:
                sz=sizes.get(dst,0)
                if 4<=sz<=4096:
                    row['exact']=1;s,_=summarize(dst,exact(dol,elf,dst,sz//4))
                    for k in ('words','direct','indirect','tail','returns','mtmsr','system'):row[k]=s[k]
                else:row['restore_gprs']=leaf_alias(dol,elf,dst,sizes)
            print('V749_EDGE '+' '.join(f'{k}={v}' for k,v in row.items())+' name='+(names(elf,dst) if dst is not None else 'indirect'))
    print('V749_CENSUS verified=1 roots=4 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError):
        print('V749_CENSUS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
