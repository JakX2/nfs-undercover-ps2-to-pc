#!/usr/bin/env python3
"""Require an authenticated absent-controller frontier before callback execution."""
import argparse,re
from pathlib import Path
import audit_v1021_error_frontier as old
import audit_v1009_second_callback as prefix
import audit_v1014_second_callback_time as time
from audit_second_irq_output_v1016 import public_line
def inspect(raw,rc):
    if len(raw)>old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l.startswith((b'V1009_',b'V1014_'))]
    base=raw;done=0
    if hits:
        i=hits[0];base=b'\n'.join(rows[:i])
        tail=[l for l in rows[i:] if l.startswith(old.TAGS)]
        if len(tail)!=2 or not re.fullmatch(prefix.RESULT,tail[0]):
            return 'V1023_ERROR_CALLBACK_CENSUS verified=0 time_return=0 boot_verified=0',False
        m=re.fullmatch(time.RESULT,tail[1])
        if not m:return 'V1023_ERROR_CALLBACK_CENSUS verified=0 time_return=0 boot_verified=0',False
        lv,p,r=map(int,m.groups())
        if not (1<=p<=12 and lv==18+5*(p-1) and r==3*p):
            return 'V1023_ERROR_CALLBACK_CENSUS verified=0 time_return=0 boot_verified=0',False
        done=1
    line,ok=old.inspect(base,rc)
    if ('branch=6 admitted=1' in line)!=bool(done):ok=False
    return f'V1023_ERROR_CALLBACK_CENSUS verified={int(ok)} time_return={done if ok else 0} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1023_ERROR_CALLBACK_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),(old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,old.DETAIL,prefix.RESULT,prefix.FAULT,time.RESULT,time.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
