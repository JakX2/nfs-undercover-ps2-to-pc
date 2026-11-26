#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_second_irq_output_v1016 import public_line
import audit_v951_second_dispatch as old
BEGIN=b'V958_ACK_BEGIN original_handler=1 exclusive_device=1'
RESULT=rb'V958_ACK_RESULT original_w1c=1 next_label=1 saved_fields=38 token_preserved=1 visits=([0-9]{1,4}) reads=([0-9]{1,3}) writes=([0-9]{1,3}) boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=[1-8] stage=[0-3] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
def inspect(raw,rc):
    if len(raw)>old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(old.RESULT,l)]
    ok=False;visits=reads=writes=0
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=old.handler.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V932_',b'V939_',b'V951_',b'V958_',old.capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        m=re.fullmatch(RESULT,tail[-1]) if tail else None
        ok=bool(valid and m and tail[:-1]==[BEGIN] and 1<=int(m[1])<=8192 and int(m[2])>=1 and int(m[3])>=1 and int(m[2])+int(m[3])<=128 and not any(l.startswith(b'V958_') for l in rows[:i+1]))
        if ok:visits,reads,writes=map(int,m.groups())
    return f'V958_ACK_CENSUS rc={rc} verified={int(ok)} original_w1c={int(ok)} visits={visits} reads={reads} writes={writes} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V958_ACK_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_line(l,(BEGIN,),(RESULT,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
