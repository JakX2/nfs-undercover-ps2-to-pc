#!/usr/bin/env python3
"""Certify the observed original wireless setter frontier in continuous startup."""
import argparse,re
from pathlib import Path
import audit_v1107_postalarm_time as time
from audit_second_irq_output_v1016 import public_line
prefix=time.prefix;alarm=prefix.alarm
RESULT=b'V1111_POSTALARM_FRONTIER ordinal=3 visits=17 writes=3 zero_id=1 token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0'
DIAG=rb'V1111_POSTALARM_FRONTIER ordinal=[35] visits=[1-9][0-9]? writes=[0-3] zero_id=[01] token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0'
FAULT=rb'V1111_POSTALARM_FRONTIER_FAULT route=(0|10|11) witness=[0-7] stage=[56]'
TAGS=time.TAGS+(b'V1111_',b'V1114_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1111_',b'V1114_'))]
    prior=[i for i,l in enumerate(rows) if l.startswith(b'V1103_')]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=time.inspect(b'\n'.join(rows[:i]),0)
    return f'V1114_POSTALARM_FRONTIER_CENSUS verified={int(ok)} original_wireless_frontier={int(ok)} token_held={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1114_POSTALARM_FRONTIER_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
