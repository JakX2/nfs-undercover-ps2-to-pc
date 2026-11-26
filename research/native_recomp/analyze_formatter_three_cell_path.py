#!/usr/bin/env python3
"""Conditional three-cell path census; live guest state is not modified."""
import argparse,struct
from pathlib import Path
from audit_formatter_third_cell import plan as third_audit
from analyze_formatter_nested_path import plan as nested,candidate_map
from audit_formatter_nested_read import classify_section
from prepare_post_stm_sc_state import overlap
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

def admitted(audit,addr,blob,cells):
    if audit!=('writable',4,1,1,0,0,0,0,1):
        raise ValueError('three cell audit')
    result=(*cells,(addr,blob))
    candidate_map(None,result,third=True)
    return result

def validate(path,sites,previous,prior_sites,cells):
    if len(path)<75 or len(previous)!=74 or tuple(path[:74])!=previous or tuple(sites[:18])!=prior_sites:
        raise ValueError('three cell prefix')
    if len(cells)!=3 or len(prior_sites)!=18:
        raise ValueError('three cell geometry')
    for ordinal,(addr,blob) in zip((35,44,74),cells):
        hits=[pc for pc,k,n,a in sites if k=='const_read' and n==len(blob) and a==addr]
        if hits!=[path[ordinal]]:raise ValueError('three cell read order')
    return len(path),len(set(path))

def plan(d,e):
    audit,addr,data,cells,previous,prior_sites=third_audit(d,e,details=True)
    cells=admitted(audit,addr,data,cells)
    missed=[]
    try:path,frame,sites,words,_=nested(d,e,candidates=cells,third=True,read_refusal=lambda *args:missed.append(args))
    except ValueError:
        if len(missed)!=1:raise
        at,width,path,frame,sites,*_=missed[0]
        if len(path)<=75 or any(overlap(at,width,a,len(b)) for a,b in cells):
            raise ValueError('three cell next boundary')
        validate(path[:-1],sites,previous,prior_sites,cells)
        return 'load',path[:-1],frame,sites,0,width,classify_section(e,at,width)
    validate(path,sites,previous,prior_sites,cells)
    if frame!=48:raise ValueError('three cell frame')
    return 'call',path,frame,sites,words,0,'none'

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','three cell audit','three cell prefix','three cell geometry','three cell read order','three cell next boundary','three cell frame','nested candidate cap','nested candidate geometry','formatter stack read provenance','formatter pointer provenance','formatter unknown value','formatter unknown arithmetic','formatter duplicate stack write','formatter other boundary','formatter CR provenance','formatter CTR provenance','formatter indexed load provenance','formatter indexed load form'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            boundary,path,frame,sites,words,width,kind=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('formatter opcode '):
            _,_,k,n=reason.split()
            if k in ('integer','load','store','branch','direct','return','system_control','other') and n.isdecimal() and 1<=int(n)<=512:
                print(f'FORMATTER_THREE_CELL_PATH analyzed=0 reason=opcode category={k} ordinal={n} live_value_verified=0');return 1
        print('FORMATTER_THREE_CELL_PATH analyzed=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input')+' live_value_verified=0');return 1
    print(f'FORMATTER_THREE_CELL_PATH analyzed=1 conditional=1 visits={len(path)} unique={len(set(path))} frame={frame} loads={sum(k.endswith("_read") for _,k,_,_ in sites)} stores={sum(k=="stack_write" for _,k,_,_ in sites)} boundary={boundary} target_words={words} next_width={width} section={kind} candidate_cells=3 live_value_verified=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
