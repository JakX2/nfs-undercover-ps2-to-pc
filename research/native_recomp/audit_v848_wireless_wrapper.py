#!/usr/bin/env python3
"""Validate the continuous original wireless wrapper boundary, not EXI completion."""
import argparse,re
from pathlib import Path
from audit_v836_callback_frontier import (inspect as frontier_audit,FRONTIER_RETURN,
    FRONTIER_ENTRY,FRONTIER_FAULT,TIME_ENTRY,TIME_RETURN,TIME_FAULT,BEGIN,DONE,
    FAULT,ALARM_FAULT,START,RESULT,PREFIXES,CLASS,BLR,BOUNDARY,CONTROL,INVALID,
    ENTRY,HANDOFF,TRANSFER,prior,MAX_LOG)

WRAPPER_ENTRY=rb'V847_WIRELESS_ENTRY frontier=1 ordinal=([35]) changed=([01])'
WRAPPER_RETURN=rb'V847_WIRELESS_RESULT ordinal=([35]) changed=([01]) visits=([0-9]{1,3}) writes=([0-9]{1,2}) returned=([01]) lock_entry=([01]) exi_executed=0 callback_return=0 boot_verified=0'
WRAPPER_FAULT=rb'V847_WIRELESS_INVALID kind=[1-4] stage=[0-3] witness=[0-7] device=[0-7] visits=[0-9]{1,3} writes=[0-9]{1,2}'

def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if re.fullmatch(FRONTIER_RETURN,l)]
    ordinal=changed=visits=writes=returned=lock=0
    ok=False
    if len(hits)==1:
        i=hits[0];before=rows[:i+1]
        tail=[l for l in rows[i+1:] if l.startswith(PREFIXES+(b'V807_',b'V813_',b'V831_',b'V847_'))]
        _,valid=frontier_audit(b'\n'.join(before),0)
        if valid and rc==0 and not any(l.startswith(b'V847_') for l in before) and len(tail)==2:
            a=re.fullmatch(WRAPPER_ENTRY,tail[0]);b=re.fullmatch(WRAPPER_RETURN,tail[1])
            if a and b:
                ordinal,changed,visits,writes,returned,lock=map(int,b.groups())
                previous=int(re.fullmatch(FRONTIER_RETURN,rows[i])[1])
                ok=(tuple(map(int,a.groups()))==(ordinal,changed)
                    and ordinal==previous and 1<=visits<=320 and 0<=writes<=64 and writes<visits
                    and returned==1-changed and lock==changed and (not changed or ordinal==3))
    if not ok:ordinal=changed=visits=writes=returned=lock=0
    return (f'V848_WIRELESS_CENSUS rc={rc} frontier_verified={int(ok)} ordinal={ordinal} '
            f'changed={changed} visits={visits} writes={writes} original_return={returned} '
            f'exilock_entry={lock} verified={int(ok)} exi_executed=0 callback_return=0 boot_verified=0'),ok

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V848_WIRELESS_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l in (HANDOFF,TIME_ENTRY,FRONTIER_ENTRY) or any(re.fullmatch(p,l) for p in
            (ENTRY,TRANSFER,START,RESULT,BEGIN,DONE,FAULT,ALARM_FAULT,CLASS,BLR,BOUNDARY,CONTROL,INVALID,
             TIME_RETURN,TIME_FAULT,FRONTIER_RETURN,FRONTIER_FAULT,WRAPPER_ENTRY,WRAPPER_RETURN,WRAPPER_FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
