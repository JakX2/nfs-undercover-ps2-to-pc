#!/usr/bin/env python3
"""Strict full-image callback-prefix result audit; no unverified success."""
import argparse
import re
from pathlib import Path
from audit_v786_alarm_return import inspect as alarm, START, RESULT
from audit_v789_alarm_suffix import PREFIXES, CLASS, BLR, BOUNDARY, CONTROL, INVALID
from audit_v777_transfer_return import ENTRY, HANDOFF, RESULT as TRANSFER
from audit_v742_handler_time import diagnostic as prior, MAX_LOG

BEGIN = rb'V807_CALLBACK_ENTRY ordinal=(6|11) identity=1 follow=3'
DONE = rb'V807_CALLBACK_RESULT original_prologue=1 save_return=1 stack_writes=8 visits=13 follow=3 continuation_executed=0 callback_return=0 boot_verified=0'
FAULT = rb'V807_CALLBACK_INVALID kind=[1-4] stage=[0-6] witness=[0-4] device=[0-7] visits=[0-9]{1,2}'
ALARM_FAULT = rb'V786_ALARM_INVALID kind=[1-5] route=[0-8] queue=[0-5] mismatch=[0-6] device=[0-7] stage=[0-4] visits=[0-9]{1,3}'

def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,line in enumerate(rows) if re.fullmatch(RESULT,line)]
    ok=False;ordinal=0
    if len(hits)==1:
        i=hits[0]
        _,valid=alarm(b'\n'.join(rows[:i+1]),0)
        earlier=[l for l in rows[:i+1] if l.startswith(b'V807_')]
        tail=[l for l in rows[i+1:] if l.startswith(PREFIXES+(b'V807_',))]
        old=int(re.fullmatch(RESULT,rows[i])[7])
        if valid and not earlier and rc==0 and old in (2,3) and len(tail)==2:
            a,b=(re.fullmatch(p,l) for p,l in zip((BEGIN,DONE),tail))
            if a and b:ok=True;ordinal=int(a[1])
    return (f'V809_CALLBACK_CENSUS rc={rc} original_prefix={int(ok)} ordinal={ordinal} '
            f'save_return={int(ok)} callback_return=0 verified={int(ok)} boot_verified=0'),ok

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V809_CALLBACK_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l==HANDOFF or any(re.fullmatch(p,l) for p in
            (ENTRY,TRANSFER,START,RESULT,BEGIN,DONE,FAULT,ALARM_FAULT,CLASS,BLR,BOUNDARY,CONTROL,INVALID)):
            print(l.decode())
    print(row)
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
