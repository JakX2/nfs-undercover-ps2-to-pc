#!/usr/bin/env python3
"""Audit the third boundary's initialized data; never admit its live value."""
import argparse,struct
from pathlib import Path
from analyze_formatter_two_cell_path import plan as two_cell_path
from analyze_formatter_nested_candidate import protected_ranges
from audit_formatter_nested_read import audit_cell
from prepare_post_stm_sc_state import overlap
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def classify(record,data,addr,cells,protected):
    kind,n,mapped,equal,covered,matches,writers=record
    if n!=4 or addr&3 or not 0x80000000<=addr<addr+n<=0x81800000 or len(cells)!=2:
        raise ValueError('third cell geometry')
    if any(overlap(addr,n,a,len(blob)) for a,blob in cells):
        raise ValueError('third cell predecessor overlap')
    protected_overlap=int(any(overlap(addr,n,a,m) for a,m in protected))
    eligible=int(kind=='writable' and mapped==equal==1 and isinstance(data,bytes) and len(data)==n and not protected_overlap and writers==0)
    # This is only an initial-file candidate. Indexed/dynamic writers
    # are not excluded by the direct SDA census, so live proof is separate.
    return (*record,protected_overlap,eligible)

def plan(d,e,*,details=False):
    kind,path,frame,sites,_,width,section,entry,record,cells=two_cell_path(d,e,details=True)
    if (kind,len(path),len(set(path)),frame,len(sites),width,section)!=('load',74,74,48,18,4,'writable'):
        raise ValueError('third cell frontier')
    addr,n=record[:2]
    audit,data=audit_cell(d,e,addr,n)
    result=classify(audit,data,addr,cells,protected_ranges(d,e))
    return (result,addr,data,cells,tuple(path),tuple(sites)) if details else result

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','third cell geometry','third cell predecessor overlap','third cell frontier','nested audit cell range'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            kind,n,mapped,equal,covered,matches,writers,protected,eligible=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_THIRD_CELL_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_THIRD_CELL_AUDIT verified=1 section={kind} width={n} dol_initialized={mapped} elf_agreement={equal} inherited_seed_bytes={covered} matching_seed_bytes={matches} earlier_direct_writers={writers} protected_overlap={protected} file_candidate={eligible} live_value_verified=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
