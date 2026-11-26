#!/usr/bin/env python3
"""Find the authenticated prefix before the first unresolved nested load.

The failing instruction is not counted as executed. No candidate bytes are
supplied, and no private instruction, address or value leaves this process.
"""
import argparse,struct
from pathlib import Path
from analyze_formatter_nested_path import plan as nested
from audit_osinit_suffix_v929 import category
from prepare_v419_full_start import MAX_DOL
from audit_formatter_nested_read import classify_section

def validate(record):
    at,n,path,frame,sites,gp,mem,cr,ctr,lr,saves=record
    if n not in (1,2,4) or at%n or not 0x80000000<=at<at+n<=0x81800000:
        raise ValueError('frontier read geometry')
    if not 1<len(path)<=512 or len(gp)!=32 or frame!=48 or gp[1][0]!='stack':
        raise ValueError('frontier prefix geometry')
    if any(pc==path[-1] for pc,*_ in sites) or path[-1] in path[:-1]:
        raise ValueError('frontier unresolved instruction repeated')
    if not any(k=='stack_write' for _,k,_,_ in sites):
        raise ValueError('frontier frame missing')
    return len(path)-1,len(set(path[:-1])),frame,sites,n,len(saves)

def plan(d,e,*,details=False):
    missed=[];entries=[]
    try:nested(d,e,read_refusal=lambda *args:missed.append(args),entry_observer=lambda *args:entries.append(args))
    except ValueError:
        if len(missed)!=1 or len(entries)!=1:raise ValueError('frontier refusal')
    else:raise ValueError('frontier no refusal')
    result=validate(missed[0]),classify_section(e,missed[0][0],missed[0][1])
    return (*result,entries[0],missed[0]) if details else result

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','frontier read geometry','frontier prefix geometry','frontier unresolved instruction repeated','frontier frame missing','frontier refusal','frontier no refusal'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        (visits,unique,frame,sites,width,saved),kind=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_NESTED_FRONTIER verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_NESTED_FRONTIER verified=1 prefix_visits={visits} unique={unique} frame={frame} loads={sum(k.endswith("_read") for _,k,_,_ in sites)} stores={sum(k=="stack_write" for _,k,_,_ in sites)} saved={saved} boundary_read_width={width} section={kind} live_value_verified=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
