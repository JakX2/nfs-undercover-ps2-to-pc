#!/usr/bin/env python3
"""Locate the next unresolved load under exactly one conditional file value."""
import argparse,struct
from pathlib import Path
from analyze_formatter_nested_candidate import candidate
from analyze_formatter_nested_path import plan as nested
from audit_formatter_nested_read import classify_section
from prepare_post_stm_sc_state import overlap
from prepare_v419_full_start import MAX_DOL
from make_v1243_stm_fixture import data_at
from prepare_post_stm_sc_version import elf_data

def summarize(cell,record):
    addr,data=cell
    at,n,path,frame,sites,gp,mem,cr,ctr,lr,saves=record
    if n not in (1,2,4) or at%n or not 0x80000000<=at<at+n<=0x81800000:
        raise ValueError('second frontier range')
    if overlap(addr,len(data),at,n):
        raise ValueError('second frontier overlap')
    if len(path)<=36 or len(path)>512 or frame!=48 or len(gp)!=32 or gp[1][0]!='stack':
        raise ValueError('second frontier geometry')
    if path[-1] in path[:-1] or any(pc==path[-1] for pc,*_ in sites):
        raise ValueError('second frontier unresolved visit')
    reads=[pc for pc,k,width,a in sites if k=='const_read' and a==addr and width==len(data)]
    if len(reads)!=1 or reads[0]!=path[35]:
        raise ValueError('second frontier predecessor')
    return len(path)-1,len(set(path[:-1])),len(path)-36,frame,sites,n

def plan(d,e,*,details=False):
    cell=candidate(d,e);missed=[];entries=[]
    try:nested(d,e,candidate=cell,read_refusal=lambda *args:missed.append(args),entry_observer=lambda *args:entries.append(args))
    except ValueError:
        if len(missed)!=1 or len(entries)!=1:raise ValueError('second frontier refusal')
    else:raise ValueError('second frontier no refusal')
    record=missed[0];counts=summarize(cell,record)
    at,n=record[:2];kind=classify_section(e,at,n)
    blob=data_at(d,at,n)
    equal=False
    if blob is not None and kind in ('writable','readonly'):
        try:equal=elf_data(e,at,n)==blob
        except ValueError:pass
    result=(counts,kind,int(blob is not None),int(equal))
    return (*result,entries[0],record,cell) if details else result

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','second frontier range','second frontier overlap','second frontier geometry','second frontier unresolved visit','second frontier predecessor','second frontier refusal','second frontier no refusal'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        (visits,unique,additional,frame,sites,width),kind,mapped,equal=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_SECOND_FRONTIER analyzed=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input')+' live_value_verified=0');return 1
    print(f'FORMATTER_SECOND_FRONTIER analyzed=1 conditional=1 visits={visits} unique={unique} additional={additional} frame={frame} loads={sum(k.endswith("_read") for _,k,_,_ in sites)} stores={sum(k=="stack_write" for _,k,_,_ in sites)} next_width={width} section={kind} dol_initialized={mapped} elf_agreement={equal} candidate_cells=1 live_value_verified=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
