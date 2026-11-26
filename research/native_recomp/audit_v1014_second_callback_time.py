#!/usr/bin/env python3
"""Require a verified second prefix before its original time-helper return."""
import argparse,re,tempfile,sys
from pathlib import Path
import audit_v1009_second_callback as old
RESULT=rb'V1014_CALLBACK_TIME original_return=1 leaves=3 system_visits=25 leaf_visits=([0-9]{1,3}) polls=([0-9]{1,3}) reads=([0-9]{1,3}) offset=1 token_preserved=1 saved_fields=38 continuation_executed=0 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=15 stage=[0-4] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
def inspect(raw,rc):
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l.startswith(b'V1014_')]
    prior=raw;done=0
    if hits:
        if len(hits)!=1:return 'V1014_CALLBACK_TIME_CENSUS verified=0 time_return=0 boot_verified=0',False,raw
        i=hits[0];m=re.fullmatch(RESULT,rows[i])
        if not m or any(l.startswith(old.old.TAGS+(b'V1009_',b'V1014_')) for l in rows[i+1:]):
            return 'V1014_CALLBACK_TIME_CENSUS verified=0 time_return=0 boot_verified=0',False,raw
        prior=b'\n'.join(rows[:i]);lv,p,r=map(int,m.groups())
        if not (1<=p<=12 and lv==18+5*(p-1) and r==3*p):
            return 'V1014_CALLBACK_TIME_CENSUS verified=0 time_return=0 boot_verified=0',False,prior
        done=1
    line,ok,_=old.inspect(prior,rc)
    if ('prefix=1' in line)!=bool(done):ok=False
    return f'V1014_CALLBACK_TIME_CENSUS verified={int(ok)} time_return={done if ok else 0} boot_verified=0',ok,prior
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.shared.old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok,prior=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1014_CALLBACK_TIME_AUDIT inspected=0');return 1
    with tempfile.TemporaryDirectory() as td:
        log=Path(td)/'prior';log.write_bytes(prior)
        previous=sys.argv;sys.argv=[previous[0],str(log),str(a.rc)]
        try:old.main()
        finally:sys.argv=previous
    for line in raw.splitlines():
        if re.fullmatch(RESULT,line) or re.fullmatch(FAULT,line):print(line.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
