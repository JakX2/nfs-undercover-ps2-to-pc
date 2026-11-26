#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_second_irq_output_v1016 import public_line
import audit_v958_second_ack as ack
import audit_v967_post_ack as post
import audit_v967_post_ack as old
RESULT=rb'V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits=([0-9]{1,4}) handler_instruction_executed=0 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=(?:[1-9]|10) stage=[0-4] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
def inspect(raw,rc):
    if len(raw)>old.old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(old.RESULT,l)]
    ok=False;visits=0
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=old.old.old.handler.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V932_',b'V939_',b'V951_',b'V958_',b'V967_',b'V975_',old.old.old.capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        m=re.fullmatch(RESULT,tail[0]) if len(tail)==1 else None
        ok=bool(valid and m and 1<=int(m[1])<=8192 and not any(l.startswith(b'V975_') for l in rows[:i+1]))
        if ok:visits=int(m[1])
    return f'V975_TIME_CENSUS rc={rc} verified={int(ok)} original_time_return={int(ok)} visits={visits} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V975_TIME_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_line(l,(ack.BEGIN,),(RESULT,FAULT,post.RESULT,post.FAULT,ack.RESULT,ack.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
