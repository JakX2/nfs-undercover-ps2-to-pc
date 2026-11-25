#!/usr/bin/env python3
"""Private dependency census for the established SI type callback candidate."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER,shape
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE,TIME,SCHED
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import names,summarize,edge
from audit_handler_deps_v749 import graph,leaf_alias
from audit_si_deep_v695 import census
from si_nested_geometry_v693 import nested_plan
from classify_save_leaf_v683 import inspect_suffix,symbol_evidence
CALLBACK=0x805327f8 # established by V529 original discovery argument
def callback_sites(root,words):
    _,direct,indirect=shape(root,words)
    calls=sorted([*direct,*[(pc,None) for pc in indirect]])
    result=[]
    for ordinal,(pc,dst) in enumerate(calls,1):
        if dst is None:
            w=words[(pc-root)//4]
            if w!=0x4e800421:raise ValueError('indirect form')
            result.append((ordinal,pc))
    return result
def inspect(dol,elf):
    sizes=parse_functions(elf);n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    sites=callback_sites(HANDLER,handler)
    if [i for i,_ in sites]!=[6,11]:raise ValueError('handler indirect geometry')
    size=sizes.get(CALLBACK,0)
    if not 4<=size<=4096 or size&3:raise ValueError('callback extent')
    code=exact(dol,elf,CALLBACK,size//4)
    name=names(elf,CALLBACK)
    if name not in ('GetTypeCallback','SIGetTypeCallback','SIGetTypeAsyncCallback','unclassified'):raise ValueError('callback identity')
    summary,_=summarize(CALLBACK,code)
    counts,first=census(CALLBACK,code)
    print('V787_CALLBACK_ROOT name='+name+' '+' '.join(f'{k}={v}' for k,v in summary.items()))
    print(f'V787_CALLBACK_PREFIX first_calls={len(first)} '+' '.join(f'{k}={v}' for k,v in counts.items()))
    known={DISABLE:1,RESTORE:2,TIME:3,SCHED:4,nested_plan(dol,elf)[1]:5,CALLBACK:6}
    for i in (4,5,7,8):known[edge(HANDLER,handler,i)[1]]=i+10
    ordinal=0
    for kind,dst in graph(CALLBACK,code):
        if kind!=3:ordinal+=1
        row=dict(ordinal=ordinal if kind!=3 else 0,kind=kind,known=known.get(dst,0),first=int(kind!=3 and ordinal in first),exact=0,words=0,direct=0,indirect=0,tail=0,returns=0,mtmsr=0,system=0,restore_gprs=0,save_gprs=0)
        if dst is not None:
            sz=sizes.get(dst,0)
            if 4<=sz<=4096 and not sz&3:
                child=exact(dol,elf,dst,sz//4);s,_=summarize(dst,child)
                row['exact']=1
                for k in ('words','direct','indirect','tail','returns','mtmsr','system'):row[k]=s[k]
            else:
                row['restore_gprs']=leaf_alias(dol,elf,dst,sizes)
                if sum(a<dst<a+n for a,n in sizes.items())==1:
                    ev=symbol_evidence(elf,dst)
                    if ev['zero_func'] or ev['notype']:
                        try:
                            q=inspect_suffix(dol,elf,dst)
                            if q['kind']==1:row['save_gprs']=q['registers']
                        except ValueError:pass
        print('V787_CALLBACK_EDGE '+' '.join(f'{k}={v}' for k,v in row.items())+' name='+(names(elf,dst) if dst is not None else 'indirect'))
    print('V787_CALLBACK_CENSUS verified=1 indirect_sites=2 known_candidate=1 dynamic_target=0 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('indirect form','handler indirect geometry','callback extent','callback identity','size')
        print('V787_CALLBACK_CENSUS verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
