#!/usr/bin/env python3
"""Audit the optional live callback-return route without treating a stop as a boot."""
import argparse
import re
from pathlib import Path
from audit_v848_wireless_wrapper import (
    inspect as wrapper_audit,WRAPPER_ENTRY,WRAPPER_RETURN,WRAPPER_FAULT,
    FRONTIER_ENTRY,FRONTIER_RETURN,FRONTIER_FAULT,TIME_ENTRY,TIME_RETURN,TIME_FAULT,
    BEGIN,DONE,FAULT,ALARM_FAULT,START,RESULT,PREFIXES,CLASS,BLR,BOUNDARY,CONTROL,
    INVALID,ENTRY,HANDOFF,TRANSFER,prior,MAX_LOG)

SUFFIX_ENTRY=rb'V850_CALLBACK_SUFFIX_ENTRY setter_return=1 handler_ordinal=(6|11)'
SUFFIX_RETURN=rb'V850_CALLBACK_SUFFIX_RESULT ordinal=(4|13) target_class=([0-4]) visits=([0-9]{1,3}) writes=([0-8]) polls=([0-9]{1,3}) setter_return=1 callback_return=0 boot_verified=0'
CALLBACK_RETURN=rb'V850_CALLBACK_RETURN_RESULT handler_ordinal=(6|11) restore=1 callback_return=1 abi=1 outer_dispatch=1 visits=12 handler_instruction_executed=0 boot_verified=0'
CALLBACK_FAULT=rb'V850_CALLBACK_RETURN_INVALID kind=[1-7] suffix_stage=[0-2] suffix_reason=[0-7] return_stage=[0-5] return_reason=[0-6] device=[0-7]'
TAGS=PREFIXES+(b'V807_',b'V813_',b'V831_',b'V847_',b'V850_')

def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if re.fullmatch(WRAPPER_RETURN,l)]
    ok=False;handler=ordinal=changed=boundary=returned=lock=visits=writes=polls=0
    if len(hits)==1 and rc==0:
        i=hits[0]
        before=rows[:i+1]
        tail=[l for l in rows[i+1:] if l.startswith(TAGS)]
        _,valid=wrapper_audit(b'\n'.join(before),0)
        handlers=[int(m[1]) for l in before if (m:=re.fullmatch(BEGIN,l))]
        if valid and len(handlers)==1 and not any(l.startswith(b'V850_') for l in before):
            handler=handlers[0]
            ordinal,changed,_,_,wrapper_return,lock=map(int,re.fullmatch(WRAPPER_RETURN,rows[i]).groups())
            # These routes still have an explicit bounded stop, not a callback return.
            if lock or ordinal==5:
                ok=not tail
            elif ordinal==3 and not changed and wrapper_return and len(tail) in (2,3):
                e=re.fullmatch(SUFFIX_ENTRY,tail[0]);s=re.fullmatch(SUFFIX_RETURN,tail[1])
                if e and s and int(e[1])==handler:
                    boundary,target,visits,writes,polls=map(int,s.groups())
                    if 1<=visits<=128 and writes<visits and polls<visits:
                        if boundary==4:
                            ok=1<=target<=4 and len(tail)==2
                        elif boundary==13 and target==0 and len(tail)==3:
                            r=re.fullmatch(CALLBACK_RETURN,tail[2])
                            ok=bool(r and int(r[1])==handler)
                            returned=int(ok)
    if not ok:handler=ordinal=changed=boundary=returned=lock=visits=writes=polls=0
    return (f'V852_CALLBACK_RETURN_CENSUS rc={rc} verified={int(ok)} handler_ordinal={handler} '
            f'wireless_ordinal={ordinal} changed={changed} exilock_entry={lock} suffix_boundary={boundary} '
            f'suffix_visits={visits} suffix_writes={writes} suffix_polls={polls} '
            f'callback_return={returned} outer_dispatch={returned} handler_instruction_executed=0 boot_verified=0'),ok

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V852_CALLBACK_RETURN_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l in (HANDOFF,TIME_ENTRY,FRONTIER_ENTRY) or any(re.fullmatch(p,l) for p in
            (ENTRY,TRANSFER,START,RESULT,BEGIN,DONE,FAULT,ALARM_FAULT,CLASS,BLR,BOUNDARY,CONTROL,INVALID,
             TIME_RETURN,TIME_FAULT,FRONTIER_RETURN,FRONTIER_FAULT,WRAPPER_ENTRY,WRAPPER_RETURN,WRAPPER_FAULT,
             SUFFIX_ENTRY,SUFFIX_RETURN,CALLBACK_RETURN,CALLBACK_FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
