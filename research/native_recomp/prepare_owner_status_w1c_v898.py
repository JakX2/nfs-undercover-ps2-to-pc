#!/usr/bin/env python3
"""Private original resumed SI handler prefix, through exact status load."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v868_handler_suffix import lane
from audit_handler_path_v887 import unique_prefix
from audit_handler_frontier_v896 import paths
from prepare_owner_restore_v735 import H,BLR,caller,header,install
from prepare_owner_cancel_v754 import patch_analyzer

def plan(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf);start=sites[0]+4
    rows=lane(HANDLER,words,start,(52,0,1,((1,7),(1,8),(1,12))))
    if unique_prefix(rows,start)[0]!='si_status':raise ValueError('status identity')
    code=[rows[start+4*i][0] for i in range(10)]
    if [w>>26 for w in code] != [15,15,21,15,31,32,21,14,31,36] or (code[4]>>1)&1023!=792:raise ValueError('status prefix shape')
    if paths(rows,start,10)!=[('store','si_status',36)] or any(rows[start+4*i][1:]!=(0,0) for i in range(10)):raise ValueError('status store identity')
    return start,code+[BLR],0,0

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());root,code,_,_=q
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(({H:caller(root),root:code},),a.output)
        else:
            header(q,a.output);print('V898_STATUS_GEOMETRY verified=1 prefix=5 original_load=1 original_store=1 synthetic_stop=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('status store identity','status identity','status prefix shape','native coverage','caller owner','hook identity','include','hook coverage','private output')
        print('V898_STATUS_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
