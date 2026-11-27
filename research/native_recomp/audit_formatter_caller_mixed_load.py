#!/usr/bin/env python3
"""Aggregate-only load provenance after the mixed caller continuation."""
import argparse,struct
from pathlib import Path
from prepare_formatter_caller_mixed_contract import plan as mixed_plan
from audit_formatter_caller_load import audit_live
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from analyze_formatter_nested_path import immutable_read
from audit_formatter_nested_read import classify_section
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def audit(contract,live,mem,initial,parent,admitted,*,resolve=None,section=None):
    blocks,rows,pc,w=contract
    if len(rows)!=5 or sum(x[4] is None for x in rows)!=2 or sum(x[5] is True for x in rows)!=2 or sum(x[5] is False for x in rows)!=1:
        raise ValueError('mixed load predecessor')
    if rows[-1][3]!=pc or boundary_shape(w)!='load':
        raise ValueError('mixed load boundary')
    owners=[(a,b) for a,b in blocks.items() if not pc&3 and a<=pc<a+4*len(b)]
    if len(owners)!=1 or owners[0][1][(pc-owners[0][0])//4]!=w:
        raise ValueError('mixed load boundary')
    return audit_live(w,live,mem,initial,parent,admitted,resolve=resolve,section=section)

def plan(d,e):
    contract,_,live,_=mixed_plan(d,e)
    _,_,trace,admitted,entry,_=replay_plan(d,e,details=True)
    _,_,_,mem=trace[-1];_,initial,parent,_,_=entry
    return audit(contract,live,mem,initial,parent,admitted,resolve=lambda a,n:immutable_read(d,e,a,n),section=lambda a,n:classify_section(e,a,n))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','mixed load predecessor','mixed load boundary','caller load state','caller load family'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():region,n,inherited,outputs,present,opaque,value,dest,update=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_MIXED_LOAD_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_MIXED_LOAD_AUDIT verified=1 region={region} width={n} inherited_bytes={inherited} child_output_bytes={outputs} established_bytes={present} opaque_bytes={opaque} value_kind={value} destination={dest} update={update} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
