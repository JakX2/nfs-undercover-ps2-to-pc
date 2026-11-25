#!/usr/bin/env python3
"""Require original full-image callback prefix AND exact system time return."""
import argparse,re
from pathlib import Path
from audit_v809_callback_prefix import inspect as prefix,BEGIN,DONE,FAULT,ALARM_FAULT
from audit_v786_alarm_return import START,RESULT
from audit_v789_alarm_suffix import PREFIXES,CLASS,BLR,BOUNDARY,CONTROL,INVALID
from audit_v777_transfer_return import ENTRY,HANDOFF,RESULT as TRANSFER
from audit_v742_handler_time import diagnostic as prior,MAX_LOG

TIME_ENTRY=b'V813_CALLBACK_TIME_ENTRY prefix=1 follow=3'
TIME_RETURN=rb'V813_CALLBACK_TIME_RESULT original_return=1 abi=1 leaves=3 system_visits=25 leaf_visits=([0-9]{1,3}) polls=([0-9]{1,3}) reads=([0-9]{1,3}) offset=1 follow=3 continuation_executed=0 callback_return=0 boot_verified=0'
TIME_FAULT=rb'V813_CALLBACK_TIME_INVALID kind=[1-4] stage=[0-5] witness=[0-7] device=[0-7] visits=[0-9]{1,3} cursor=[0-3]'

def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if re.fullmatch(DONE,l)]
    ok=False;ordinal=0;leaves=0;polls=0;reads=0
    if len(hits)==1:
        i=hits[0]
        earlier=[l for l in rows[:i+1] if l.startswith(b'V813_')]
        tail=[l for l in rows[i+1:] if l.startswith(PREFIXES+(b'V807_',b'V813_'))]
        _,valid=prefix(b'\n'.join(rows[:i+1]),0)
        if valid and rc==0 and not earlier and len(tail)==2 and tail[0]==TIME_ENTRY:
            m=re.fullmatch(TIME_RETURN,tail[1])
            if m:
                lv,p,r=map(int,m.groups())
                # Original OS leaves are 5,6,9 words. The timebase
                # retry executes four additional instructions per poll,
                # and three additional timebase reads.
                if 1<=p<=32 and lv==20+4*(p-1) and r==3*p:
                    entries=[re.fullmatch(BEGIN,l) for l in rows[:i] if re.fullmatch(BEGIN,l)]
                    if len(entries)==1:
                        ok=True;ordinal=int(entries[0][1]);leaves=3;polls=p;reads=r
    return (f'V822_CALLBACK_TIME_CENSUS rc={rc} original_time_return={int(ok)} ordinal={ordinal} '
            f'leaves={leaves} polls={polls} reads={reads} offset={int(ok)} verified={int(ok)} callback_return=0 boot_verified=0'),ok

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V822_CALLBACK_TIME_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l in (HANDOFF,TIME_ENTRY) or any(re.fullmatch(p,l) for p in
            (ENTRY,TRANSFER,START,RESULT,BEGIN,DONE,FAULT,ALARM_FAULT,CLASS,BLR,BOUNDARY,CONTROL,INVALID,TIME_RETURN,TIME_FAULT)):
            print(l.decode())
    print(row)
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
