#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v777_transfer_return import inspect as transfer,RESULT as TRANSFER,ENTRY,HANDOFF,PREFIX
from audit_v742_handler_time import diagnostic as prior,MAX_LOG
from audit_v778_transfer_suffix import inspect as suffix,BOUNDARY,BLR
START=rb'V786_ALARM_ENTRY lane=([0-4]) timer=([01])'
RESULT=rb'V786_ALARM_RESULT original_return=1 queue=1 abi=1 lane=([0-4]) timer=([01]) deferred=([01]) calls=([0-9]{1,3}) visits=([0-9]{1,3}) polls=([0-9]{1,3}) follow=([023]) handler_instruction_executed=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(TRANSFER,l)]
    ok=False;lane=0;boundary=False
    if len(hits)==1:
        i=hits[0];_,valid=transfer(b'\n'.join(rows[:i+1]),0)
        tail=[l for l in rows[i+1:] if l.startswith(PREFIX+(b'V786_',b'V778_',b'V726_HANDLER_',b'V747_NEXT_'))]
        if valid and rc==0 and len(tail)==2:
            a,b=(re.fullmatch(p,l) for p,l in zip((START,RESULT),tail))
            if a and b:
                lane,timer,deferred,calls,visits,polls,follow=map(int,b.groups())
                old=int(re.fullmatch(TRANSFER,rows[i])[5])
                held=(old==follow==0) or (old==2 and follow in (2,3)) or (old==follow==3)
                masks=(3,65) if lane!=4 else (77,85,101)
                ok=bool(a.groups()==b.groups()[:2] and timer==int(lane==4) and deferred<=timer and calls in masks and
                    2<=visits<=256 and polls<=visits and held)
        elif valid and not any(l.startswith(b'V786_') for l in tail):
            _,boundary=suffix(raw,rc)
    return f'V786_ALARM_CENSUS rc={rc} original_return={int(ok)} lane={lane if ok else 0} later_boundary={int(boundary)} verified={int(ok or boundary)} boot_verified=0',ok or boundary
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V786_ALARM_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l==HANDOFF or any(re.fullmatch(p,l) for p in (ENTRY,TRANSFER,START,RESULT,BOUNDARY,BLR,rb'V786_ALARM_INVALID kind=[1-5] route=[0-8] queue=[0-5] mismatch=[0-6] device=[0-7] stage=[0-4] visits=[0-9]{1,3}')):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
