#!/usr/bin/env python3
"""Authenticate the actual original diagnostic output callback and its boundaries."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_resume import plan as resume_plan
from prepare_post_stm_sc_report_formatter import closure
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import category

def census(root,ws):
    seen,bounds,back=closure(root,ws)
    kinds={}
    for pc in seen:
        w=ws[(pc-root)//4];k=category(w);kinds[k]=kinds.get(k,0)+1
    terminals=[]
    for pc in sorted(bounds):
        w=ws[(pc-root)//4]
        if w==0x4e800020:terminals.append(('return',0))
        elif w>>26==18 and w&3==1:terminals.append(('direct',direct_bl(w,pc)))
        else:terminals.append(('other',0))
    return len(seen),kinds,back,terminals

def plan(d,e):
    _,_,_,_,_,_,_,root,_=resume_plan(d,e,details=True)
    sizes=parse_functions(e)
    if sizes.get(root)!=88:raise ValueError('callback extent')
    ws=exact_words(d,e,root,22)
    n,kinds,back,terms=census(root,ws)
    targets=[]
    for k,dst in terms:
        if k!='direct':continue
        size=sizes.get(dst,0)
        if not 4<=size<=65536 or size%4:raise ValueError('callback target')
        exact_words(d,e,dst,1);targets.append(size//4)
    return n,kinds,back,terms,targets

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','callback extent','callback target','formatter escape','formatter region cap','formatter branch','formatter boundary'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        n,kinds,back,terms,targets=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_CALLBACK_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_CALLBACK_GEOMETRY verified=1 words=22 initial_region={n} backward={back} direct_calls={len(targets)} returns={sum(k=="return" for k,_ in terms)} other_boundaries={sum(k=="other" for k,_ in terms)} original_execution=0')
    print('POST_STM_SC_REPORT_CALLBACK_CLASSES '+' '.join(f'{k}={v}' for k,v in sorted(kinds.items())))
    for i,n in enumerate(targets,1):print(f'POST_STM_SC_REPORT_CALLBACK_TARGET ordinal={i} words={n}')
    return 0
if __name__=='__main__':raise SystemExit(main())
