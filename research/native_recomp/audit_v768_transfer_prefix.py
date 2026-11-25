#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v742_handler_time import inspect as time,diagnostic as prior,RESULT as TIME_RESULT,MAX_LOG
PREFIX=b'V768_TRANSFER_'
ENTRY=rb'V768_TRANSFER_ENTRY channel=[0-3] type=1 idle=[01]'
RESULT=rb'V768_TRANSFER_RESULT original_entry=1 save=1 disable=1 boundary=([1-3]) visits=([1-9][0-9]{0,2}) mmio_executed=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(TIME_RESULT,l)]
    events=[l for l in rows if l.startswith(PREFIX)];ok=False;boundary=0
    if len(hits)==1 and len(events)==2:
        i=hits[0];_,valid=time(b'\n'.join(rows[:i+1]),0)
        m=re.fullmatch(RESULT,events[1])
        ok=bool(rc==0 and valid and re.fullmatch(ENTRY,events[0]) and m and int(m[2])<=192 and not any(l.startswith(PREFIX) for l in rows[:i+1]))
        if ok:boundary=int(m[1])
    return f'V768_TRANSFER_CENSUS rc={rc} native_prefix={int(ok)} boundary={boundary} mmio_executed=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V768_TRANSFER_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or re.fullmatch(ENTRY,l) or re.fullmatch(RESULT,l) or re.fullmatch(rb'V768_TRANSFER_INVALID kind=[1-6] reason=[0-7] stage=[0-3] visits=[0-9]{1,3} trace=[0-9]{1,2}',l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
