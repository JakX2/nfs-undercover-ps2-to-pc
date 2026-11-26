#!/usr/bin/env python3
"""Private first diagnostic dependency control/data census, no original execution."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_fixture import plan as helper_plan
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import category
from audit_handler_suffix_v728 import target
from prepare_v1377_stm_tail import scan

def census(root,words):
    if not 4<=len(words)<=128:raise ValueError('dependency extent')
    edges={root+4*i:direct_bl(w,root+4*i) for i,w in enumerate(words) if w>>26==18 and w&3==1}
    reach,calls,returns,_,_=scan(root,words,root,edges)
    rows={pc:words[(pc-root)//4] for pc in reach}
    counts={k:sum(category(w)==k for w in rows.values()) for k in ('integer','load','store','branch','direct','return','system_control','other')}
    loads={k:sum(category(w)=='load' and ((w>>16)&31) in bases for w in rows.values())
           for k,bases in (('stack',(1,)),('sda',(2,13)),('argument',(3,4,5,6,7,8,9,10)))}
    stores={k:sum(category(w)=='store' and ((w>>16)&31) in bases for w in rows.values())
            for k,bases in (('stack',(1,)),('sda',(2,13)),('argument',(3,4,5,6,7,8,9,10)))}
    back=sum(w>>26 in (16,18) and not(w&3) and target(pc,w)<=pc for pc,w in rows.items())
    first=root
    while first in rows and category(rows[first]) in ('integer','load','store'):first+=4
    if first not in rows:raise ValueError('dependency first boundary')
    return edges,rows,returns,counts,loads,stores,back,first

def plan(d,e):
    prior=helper_plan(d,e);root=prior[3][2]
    sizes=parse_functions(e)
    if sizes.get(root)!=132:raise ValueError('dependency extent')
    ws=exact_words(d,e,root,33)
    edges,rows,returns,counts,loads,stores,back,first=census(root,ws)
    deps=[]
    for site,dst in sorted(edges.items()):
        size=sizes.get(dst,0)
        if not 4<=size<=65536 or size%4:raise ValueError('dependency target')
        exact_words(d,e,dst,1);deps.append(size//4)
    return rows,returns,counts,loads,stores,back,(first-root)//4+1,category(rows[first]),deps

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','dependency extent','dependency first boundary','dependency target','tail extent','tail escape','tail call','tail control','tail reachability'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        rows,returns,counts,loads,stores,back,first,kind,deps=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_DEPENDENCY_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_DEPENDENCY_GEOMETRY verified=1 reachable={len(rows)} returns={len(returns)} calls={len(deps)} backward={back} first_ordinal={first} first_kind={kind} original_execution=0')
    print('POST_STM_SC_REPORT_DEPENDENCY_CLASSES '+' '.join(f'{k}={v}' for k,v in counts.items()))
    print('POST_STM_SC_REPORT_DEPENDENCY_MEMORY '+' '.join(f'{k}_loads={loads[k]} {k}_stores={stores[k]}' for k in loads))
    for i,n in enumerate(deps,1):print(f'POST_STM_SC_REPORT_DEPENDENCY_TARGET ordinal={i} words={n}')
    return 0
if __name__=='__main__':raise SystemExit(main())
