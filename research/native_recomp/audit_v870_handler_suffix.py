#!/usr/bin/env python3
"""Audit V868 only after the genuine original callback's verified return."""
import argparse,re
from pathlib import Path
from audit_v864_combined_callback import (
    inspect as callback_audit,TAGS as PREVIOUS,MAX_LOG,prior,HANDOFF,TIME_ENTRY,FRONTIER_ENTRY,
    ENTRY,TRANSFER,START,RESULT,BEGIN,DONE,FAULT,ALARM_FAULT,CLASS,BLR,BOUNDARY,CONTROL,INVALID,
    TIME_RETURN,TIME_FAULT,FRONTIER_RETURN,FRONTIER_FAULT,WRAPPER_ENTRY,WRAPPER_RETURN,WRAPPER_FAULT,
    FAULT_EXT,WRITE_RETURN,FAULT_WRITE,SUFFIX_ENTRY,SUFFIX_RETURN,CALLBACK_RETURN,CALLBACK_FAULT)
TAGS=PREVIOUS+(b'V868_',)
JOIN=rb'V868_HANDLER_SUFFIX_ENTRY ordinal=(6|11) callback_return=1 same_tick=1'
STOP=rb'V868_HANDLER_SUFFIX_RESULT after=(6|11) next=(7|8|11|12) kind=([12]) visits=([0-9]{1,3}) writes=([0-8]) executed=0 handler_return=0 boot_verified=0'
BAD=rb'V868_HANDLER_SUFFIX_INVALID reason=[1-6] guard=[0-5] handler=[0-8] visits=[0-9]{1,3} writes=[0-9]{1,2}'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if re.fullmatch(CALLBACK_RETURN,l)]
    ok=False;returned=handler=next_slot=kind=visits=writes=0
    previous=''
    if rc==0 and len(hits)<=1:
        if not hits:
            previous,ok=callback_audit(raw,rc)
            ok=ok and not any(l.startswith(b'V868_') for l in rows)
        else:
            i=hits[0];before=rows[:i+1]
            previous,valid=callback_audit(b'\n'.join(before),0)
            tail=[l for l in rows[i+1:] if l.startswith(TAGS)]
            if valid and len(tail)==2 and not any(l.startswith(b'V868_') for l in before):
                h=int(re.fullmatch(CALLBACK_RETURN,rows[i])[1])
                j=re.fullmatch(JOIN,tail[0]);s=re.fullmatch(STOP,tail[1])
                if j and s:
                    handler,next_slot,kind,visits,writes=map(int,s.groups())
                    allowed={(7,1),(8,1),(12,1)} if h==6 else {(11,2),(12,1)}
                    ok=h==handler==int(j[1]) and (next_slot,kind) in allowed and 1<=visits<=128 and writes<visits and writes<=(1 if h==6 else 0)
                    returned=int(ok)
    if not ok:previous='';returned=handler=next_slot=kind=visits=writes=0
    row=(f'V870_HANDLER_SUFFIX_CENSUS rc={rc} verified={int(ok)} callback_return={returned} '
         f'handler_ordinal={handler} next={next_slot} kind={kind} visits={visits} writes={writes} '
         f'handler_continuation={returned} next_call_executed=0 handler_return=0 boot_verified=0')
    return row,ok,previous
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok,previous=inspect(raw,a.rc)
    except (OSError,ValueError):print('V870_HANDLER_SUFFIX_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l in (HANDOFF,TIME_ENTRY,FRONTIER_ENTRY) or any(re.fullmatch(p,l) for p in
            (ENTRY,TRANSFER,START,RESULT,BEGIN,DONE,FAULT,ALARM_FAULT,CLASS,BLR,BOUNDARY,CONTROL,INVALID,
             TIME_RETURN,TIME_FAULT,FRONTIER_RETURN,FRONTIER_FAULT,WRAPPER_ENTRY,WRAPPER_RETURN,WRAPPER_FAULT,
             FAULT_EXT,WRITE_RETURN,FAULT_WRITE,SUFFIX_ENTRY,SUFFIX_RETURN,CALLBACK_RETURN,CALLBACK_FAULT,JOIN,STOP,BAD)):
            print(l.decode())
    if previous:print(previous)
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
