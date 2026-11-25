#!/usr/bin/env python3
"""Strict full-image post-time callback frontier audit, without private addresses."""
import argparse,re
from pathlib import Path
from audit_v822_callback_time import (inspect as time_audit,TIME_ENTRY,TIME_RETURN,TIME_FAULT,
    BEGIN,DONE,FAULT,ALARM_FAULT,START,RESULT,PREFIXES,CLASS,BLR,BOUNDARY,CONTROL,INVALID,
    ENTRY,HANDOFF,TRANSFER,prior,MAX_LOG)
FRONTIER_ENTRY=b'V831_CALLBACK_FRONTIER_ENTRY original_time_return=1 follow=3'
FRONTIER_RETURN=rb'V831_CALLBACK_FRONTIER_RESULT ordinal=([35]) visits=([0-9]{1,2}) writes=([0-3]) zero_id=([01]) follow=3 store_bytes=1 wireless_executed=0 callback_return=0 boot_verified=0'
FRONTIER_FAULT=rb'V831_CALLBACK_FRONTIER_INVALID kind=[1-4] stage=[0-2] witness=[0-7] device=[0-7] visits=[0-9]{1,2} writes=[0-4]'

def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(TIME_RETURN,l)]
    ok=False;ordinal=visits=writes=zero=handler=0
    if len(hits)==1:
        i=hits[0]
        before=rows[:i+1]
        tail=[l for l in rows[i+1:] if l.startswith(PREFIXES+(b'V807_',b'V813_',b'V831_'))]
        prior_row,valid=time_audit(b'\n'.join(before),0)
        if valid and rc==0 and not any(l.startswith(b'V831_') for l in before) and len(tail)==2 and tail[0]==FRONTIER_ENTRY:
            m=re.fullmatch(FRONTIER_RETURN,tail[1])
            if m:
                ordinal,visits,writes,zero=map(int,m.groups())
                # The private observer checked the actual original branch,
                # per-word identity, writes and same-tick device state.
                # Do not force the synthetic setter lane on the live input.
                entries=[re.fullmatch(BEGIN,l) for l in before if re.fullmatch(BEGIN,l)]
                if len(entries)==1 and 1<=visits<=27 and writes<visits and (ordinal==3 or zero==0):
                    handler=int(entries[0][1]);ok=True
    return (f'V836_CALLBACK_FRONTIER_CENSUS rc={rc} original_time_return={int(ok)} '
            f'handler_ordinal={handler if ok else 0} wireless_ordinal={ordinal if ok else 0} '
            f'visits={visits if ok else 0} writes={writes if ok else 0} zero_id={zero if ok else 0} '
            f'verified={int(ok)} wireless_executed=0 callback_return=0 boot_verified=0'),ok

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V836_CALLBACK_FRONTIER_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l in (HANDOFF,TIME_ENTRY,FRONTIER_ENTRY) or any(re.fullmatch(p,l) for p in
            (ENTRY,TRANSFER,START,RESULT,BEGIN,DONE,FAULT,ALARM_FAULT,CLASS,BLR,BOUNDARY,CONTROL,INVALID,TIME_RETURN,TIME_FAULT,FRONTIER_RETURN,FRONTIER_FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
