#!/usr/bin/env python3
"""Audit the first caller load after the nested formatter returns.

A released child frame is never treated as live parent storage. Distinguish
parent-inherited bytes, exact child output stores, and missing provenance.
"""
import argparse,struct
from pathlib import Path
from prepare_formatter_return_contract import plan as return_plan
from prepare_formatter_partial_native_contract import read_address,read_value
from audit_formatter_partial_copy import plan as replay_plan,boundary_shape
from analyze_formatter_nested_path import immutable_read
from audit_formatter_nested_read import classify_section
from make_v624_ipc_geometry import exact_words
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def audit(w,gp,mem,initial,parent,admitted,*,resolve=None,section=None):
    if len(gp)!=32 or len(initial)!=32 or initial[1][0]!='stack':
        raise ValueError('caller load state')
    sp=initial[1][1]
    if gp[1]!=('stack',sp-48) or any(mem.get(a)!=v for a,v in parent.items()):
        raise ValueError('caller load state')
    live=list(gp);live[1]=initial[1] # architectural effect of proven frame release
    return audit_live(w,live,mem,initial,parent,admitted,resolve=resolve,section=section)

def audit_live(w,live,mem,initial,parent,admitted,*,resolve=None,section=None):
    """Audit the actual post-release symbolic register state."""
    if len(live)!=32 or len(initial)!=32 or initial[1][0]!='stack' or live[1]!=initial[1] or any(mem.get(a)!=v for a,v in parent.items()):
        raise ValueError('caller load state')
    sp=initial[1][1]
    if boundary_shape(w)!='load':raise ValueError('caller load family')
    try:site=read_address(w,live)
    except ValueError:site=None
    op,rt,ra,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>1)&1023
    update=(op==31 and xo in (55,119,311,375)) or (op!=31 and bool(op&1))
    destination='nonvolatile' if rt>=14 else 'reserved' if rt in (1,2,13) else 'volatile'
    if site is None:return ('unresolved',0,0,0,0,0,'unknown',destination,int(update))
    kind,at,n=site
    if kind=='stack':
        if not sp<=at<at+n<=sp+704:
            region='released_child' if sp-48<=at<at+n<=sp else 'outside_parent'
            return region,n,0,0,0,0,'unknown',destination,int(update)
        region='parent'
        inherited=sum(at+i in parent for i in range(n))
        outputs=sum(any(a<=at+i<a+width for _,a,width,_ in admitted) for i in range(n))
        cells=tuple(mem.get(at+i) for i in range(n))
        present=sum(x is not None for x in cells)
        opaque=sum(x is not None and x[0]=='uninitialized' for x in cells)
        try:value=read_value(cells,w)[0]
        except ValueError:value='unknown'
        return region,n,inherited,outputs,present,opaque,value,destination,int(update)
    region=section(at,n) if section is not None else 'absolute'
    value='unknown';present=0
    if resolve is not None and region=='readonly':
        try:
            blob=resolve(at,n)
            if isinstance(blob,bytes) and len(blob)==n:
                value=read_value(tuple(('byte',b) for b in blob),w)[0];present=n
        except ValueError:pass
    return region,n,0,0,present,0,value,destination,int(update)

def plan(d,e):
    owner,caller,_,family,_=return_plan(d,e)
    if family!='load':raise ValueError('caller load family')
    size=parse_functions(e).get(owner,0)
    if not 4<=size<=65536 or size%4 or not owner<=caller<owner+size:raise ValueError('caller load extent')
    w=exact_words(d,e,owner,size//4)[(caller-owner)//4]
    _,_,trace,admitted,entry,_=replay_plan(d,e,details=True)
    _,_,gp,mem=trace[-1];_,initial,parent,_,_=entry
    return audit(w,gp,mem,initial,parent,admitted,resolve=lambda a,n:immutable_read(d,e,a,n),section=lambda a,n:classify_section(e,a,n))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','caller load state','caller load family','caller load extent'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():region,n,inherited,outputs,present,opaque,value,dest,update=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_CALLER_LOAD_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_CALLER_LOAD_AUDIT verified=1 region={region} width={n} inherited_bytes={inherited} child_output_bytes={outputs} established_bytes={present} opaque_bytes={opaque} value_kind={value} destination={dest} update={update} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
