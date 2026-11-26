#!/usr/bin/env python3
"""Private read-only call closure and ABI boundary census for the original report helper."""
import argparse
import struct
from pathlib import Path
from prepare_post_stm_sc_report_fixture import plan as prefix_plan
from prepare_post_stm_sc_report import REPORT
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import category
from audit_handler_suffix_v728 import target
from prepare_stm_final_return import prologue,tail
from prepare_v1377_stm_tail import scan

def census(root,words):
    if not 4<=len(words)<=128 or words[-1]!=0x4e800020:raise ValueError('report helper extent')
    edges={root+4*i:direct_bl(w,root+4*i) for i,w in enumerate(words) if w>>26==18 and w&3==1}
    reach,calls,returns,_,_=scan(root,words,root,edges)
    if len(returns)!=1:raise ValueError('report helper return')
    # Preserve a deterministic first-call boundary without assuming that
    # every call on every alternative path returns.
    first=root
    while first in reach:
        w=words[(first-root)//4]
        if category(w) in ('direct','branch','return','system_control','other'):break
        first+=4
    if first not in reach:raise ValueError('report helper first boundary')
    rows={pc:words[(pc-root)//4] for pc in reach}
    counts={k:sum(category(w)==k for w in rows.values()) for k in ('integer','load','store','branch','direct','return','system_control','other')}
    stack_loads=sum(category(w)=='load' and ((w>>16)&31)==1 for w in rows.values())
    stack_stores=sum(category(w)=='store' and ((w>>16)&31)==1 for w in rows.values())
    back=sum(w>>26 in (16,18) and not(w&3) and target(pc,w)<=pc for pc,w in rows.items())
    return edges,reach,returns,first,counts,stack_loads,stack_stores,back

def plan(d,e):
    prior=prefix_plan(d,e)
    _,root,_,_=prior[5]
    sizes=parse_functions(e)
    size=sizes.get(root,0)
    if size!=120:raise ValueError('report helper extent')
    words=exact_words(d,e,root,size//4)
    edges,reach,returns,first,counts,loads,stores,back=census(root,words)
    deps=[]
    for site,dst in sorted(edges.items()):
        n=sizes.get(dst,0)
        if not 4<=n<=65536 or n%4:raise ValueError('report helper dependency')
        exact_words(d,e,dst,1)
        deps.append((n//4,int(site==first)))
    suffix_start=max(edges)+4 if edges else root
    # The leaf suffix is authenticated independently from call return.
    suffix=tuple(words[(suffix_start-root)//4:])
    return words,counts,loads,stores,back,deps,(first-root)//4+1,category(words[(first-root)//4]),len(suffix)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','report helper extent','report helper return','report helper first boundary','report helper dependency','tail extent','tail escape','tail call','tail control','tail reachability'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        words,counts,loads,stores,back,deps,first,kind,suffix=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_HELPER_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_HELPER_GEOMETRY verified=1 words={len(words)} reachable={sum(counts.values())} calls={len(deps)} returns=1 stack_loads={loads} stack_stores={stores} backward={back} first_boundary_ordinal={first} first_boundary_kind={kind} suffix_words={suffix} original_execution=0')
    print('POST_STM_SC_REPORT_HELPER_CLASSES '+' '.join(f'{k}={v}' for k,v in counts.items()))
    for i,(n,first) in enumerate(deps,1):print(f'POST_STM_SC_REPORT_HELPER_DEP ordinal={i} target_words={n} first_boundary={first}')
    return 0
if __name__=='__main__':raise SystemExit(main())
