#!/usr/bin/env python3
"""Require actual completion-local time call between ACK and helper return."""
import argparse,re
from pathlib import Path
import audit_v967_post_ack as old
RESULT=rb'V989_SHARED_TIME_RESULT original_time=1 leaves=3 unchanged_msr=2 visits=([0-9]{1,4}) token_preserved=1 saved_fields=38 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=(?:[1-9]|1[0-2]) stage=[0-4] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
DIAG=rb'V989_SHARED_REFUSAL guard=[01] frame=[01] depth=[0-8] visits=[0-9]{1,4}'
def inspect(raw,rc):
    if len(raw)>old.old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();_,base=old.inspect(raw,rc)
    ack=[i for i,l in enumerate(rows) if re.fullmatch(old.old.RESULT,l)]
    shared=[i for i,l in enumerate(rows) if l.startswith(b'V989_')]
    post=[i for i,l in enumerate(rows) if re.fullmatch(old.RESULT,l)]
    ok=False;visits=0
    if rc==0 and base and len(ack)==len(shared)==len(post)==1 and ack[0]<shared[0]<post[0]:
        m=re.fullmatch(RESULT,rows[shared[0]]);p=re.fullmatch(old.RESULT,rows[post[0]])
        if m and 1<=int(m[1])<int(p[1])<=8192:ok=True;visits=int(m[1])
    return f'V989_SHARED_CENSUS rc={rc} verified={int(ok)} shared_time={int(ok)} original_helper_return={int(ok)} visits={visits} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V989_SHARED_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (old.old.BEGIN,old.old.old.BEGIN,*old.old.old.EDGES,old.old.old.old.TRAMP,old.old.old.old.old.SOURCE,old.old.old.old.old.RFI,old.old.old.old.old.POLL,*old.old.old.old.old.old.STAGES) or any(re.fullmatch(p,l) for p in (RESULT,FAULT,DIAG,old.RESULT,old.old.RESULT,old.old.old.RESULT,old.old.old.FAULT,old.old.old.old.RESULT,old.old.old.old.FAULT,old.old.old.old.old.RESULT,old.old.old.old.old.DIAG,old.old.old.old.old.old.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
