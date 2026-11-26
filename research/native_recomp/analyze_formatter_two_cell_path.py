#!/usr/bin/env python3
"""Conditional analysis of two authenticated file values, never live state."""
import argparse,struct
from pathlib import Path
from analyze_formatter_second_frontier import plan as second_frontier
from analyze_formatter_nested_candidate import protected_ranges
from analyze_formatter_nested_path import plan as nested,candidate_map
from audit_formatter_nested_read import classify_section
from prepare_post_stm_sc_state import overlap
from prepare_v419_full_start import MAX_DOL
from make_v1243_stm_fixture import data_at
from prepare_post_stm_sc_version import elf_data

def second_cell(first,addr,blob,protected):
    candidate_map(None,(first,(addr,blob)))
    if any(overlap(addr,len(blob),a,n) for a,n in protected):
        raise ValueError('two cell protected overlap')
    return first,(addr,blob)

def check_reads(cells,sites,path=None):
    reads=[]
    for addr,blob in cells:
        hits=[pc for pc,k,n,a in sites if k=='const_read' and n==len(blob) and a==addr]
        if len(hits)!=1:raise ValueError('two cell read identity')
        reads.append(hits[0])
    if path is not None and (len(path)<45 or reads!=[path[35],path[44]]):
        raise ValueError('two cell read order')
    return reads

def plan(d,e,*,details=False):
    counts,kind,mapped,equal,entry,record,first=second_frontier(d,e,details=True)
    if counts[:4]!=(44,44,9,48) or (kind,mapped,equal)!=('writable',1,1):
        raise ValueError('two cell predecessor')
    addr,n=record[:2];blob=data_at(d,addr,n)
    if n!=4 or blob is None or elf_data(e,addr,n)!=blob:
        raise ValueError('two cell identity')
    cells=second_cell(first,addr,blob,protected_ranges(d,e))
    missed=[];entries=[]
    try:path,frame,sites,words,extra=nested(d,e,candidates=cells,read_refusal=lambda *args:missed.append(args),entry_observer=lambda *args:entries.append(args))
    except ValueError:
        if len(missed)!=1 or len(entries)!=1:raise
        at,width,path,frame,sites,*_=missed[0]
        if len(path)<=45 or any(overlap(at,width,a,len(b)) for a,b in cells):
            raise ValueError('two cell next boundary')
        check_reads(cells,sites,path)
        result=('load',path[:-1],frame,sites,0,width,classify_section(e,at,width))
        return (*result,entries[0],missed[0],cells) if details else result
    check_reads(cells,sites,path)
    if frame!=48 or len(path)<46:raise ValueError('two cell next boundary')
    if details:raise ValueError('two cell expected load')
    return 'call',path,frame,sites,words,0,'none'

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','two cell predecessor','two cell protected overlap','two cell identity','two cell read identity','two cell read order','two cell next boundary','nested candidate cap','nested candidate geometry','nested candidate modes'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        boundary,path,frame,sites,words,width,kind=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('formatter opcode '):
            _,_,k,n=reason.split()
            if k in ('integer','load','store','branch','direct','return','system_control','other') and n.isdecimal() and 1<=int(n)<=512:
                print(f'FORMATTER_TWO_CELL_PATH analyzed=0 reason=opcode category={k} ordinal={n} live_value_verified=0');return 1
        print('FORMATTER_TWO_CELL_PATH analyzed=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input')+' live_value_verified=0');return 1
    print(f'FORMATTER_TWO_CELL_PATH analyzed=1 conditional=1 visits={len(path)} unique={len(set(path))} frame={frame} loads={sum(k.endswith("_read") for _,k,_,_ in sites)} stores={sum(k=="stack_write" for _,k,_,_ in sites)} boundary={boundary} target_words={words} next_width={width} section={kind} candidate_cells=2 live_value_verified=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
