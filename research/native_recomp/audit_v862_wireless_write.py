#!/usr/bin/env python3
"""Require a genuine original changed setter return, never just a lock entry."""
import argparse,re
from pathlib import Path
from audit_v848_wireless_wrapper import (
    inspect as wrapper_audit,WRAPPER_ENTRY,WRAPPER_RETURN,WRAPPER_FAULT,
    FRONTIER_ENTRY,FRONTIER_RETURN,FRONTIER_FAULT,TIME_ENTRY,TIME_RETURN,TIME_FAULT,
    BEGIN,DONE,FAULT,ALARM_FAULT,START,RESULT,PREFIXES,CLASS,BLR,BOUNDARY,CONTROL,
    INVALID,ENTRY,HANDOFF,TRANSFER,prior,MAX_LOG)
RETURN=rb'V861_WIRELESS_WRITE_RESULT original_setter_return=1 original_unlock=1 transfers=12 bytes=44 visits=([0-9]{1,5}) polls=([0-9]{1,4}) mmio=([0-9]{1,4}) payload=1 abi=1 callback_return=0 boot_verified=0'
FAULT_WRITE=rb'V861_WIRELESS_WRITE_INVALID kind=[1-5] device=[0-5] reason=[0-5] witness=[0-5] completed=[0-9]{1,2} bytes=[0-9]{1,2}'
FAULT_EXT=rb'V847_WIRELESS_INVALID kind=[1-4] stage=[0-3] witness=[0-9] device=[0-7] visits=[0-9]{1,5} writes=[0-9]{1,4}'
TAGS=PREFIXES+(b'V807_',b'V813_',b'V831_',b'V847_',b'V861_')

def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(WRAPPER_RETURN,l)]
    ok=False;ordinal=changed=returned=visits=polls=mmio=0
    if len(hits)==1 and rc==0:
        i=hits[0];before=rows[:i+1]
        _,valid=wrapper_audit(b'\n'.join(before),0)
        tail=[l for l in rows[i+1:] if l.startswith(TAGS)]
        if valid and not any(l.startswith(b'V861_') for l in before):
            ordinal,changed,wrapper_visits,_,wrapper_return,lock=map(int,re.fullmatch(WRAPPER_RETURN,rows[i]).groups())
            if changed and ordinal==3 and lock and len(tail)==1:
                m=re.fullmatch(RETURN,tail[0])
                if m:
                    visits,polls,mmio=map(int,m.groups())
                    ok=wrapper_visits<visits<=12000 and 1<=polls<=4096 and 1<=mmio<=4096 and polls<visits and mmio<visits
                    returned=int(ok)
            elif not changed and wrapper_return and not tail:
                # Unchanged setter and getter remain valid bounded outcomes.
                ok=True
    if not ok:ordinal=changed=returned=visits=polls=mmio=0
    return (f'V862_WIRELESS_WRITE_CENSUS rc={rc} verified={int(ok)} ordinal={ordinal} changed={changed} '
            f'original_setter_return={int(ok and ordinal==3)} changed_write_return={returned} '
            f'original_unlock={returned} transfers={12*returned} bytes={44*returned} visits={visits} polls={polls} mmio={mmio} '
            'callback_return=0 boot_verified=0'),ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V862_WIRELESS_WRITE_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l in (HANDOFF,TIME_ENTRY,FRONTIER_ENTRY) or any(re.fullmatch(p,l) for p in
            (ENTRY,TRANSFER,START,RESULT,BEGIN,DONE,FAULT,ALARM_FAULT,CLASS,BLR,BOUNDARY,CONTROL,INVALID,
             TIME_RETURN,TIME_FAULT,FRONTIER_RETURN,FRONTIER_FAULT,WRAPPER_ENTRY,WRAPPER_RETURN,WRAPPER_FAULT,
             FAULT_EXT,RETURN,FAULT_WRITE)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
