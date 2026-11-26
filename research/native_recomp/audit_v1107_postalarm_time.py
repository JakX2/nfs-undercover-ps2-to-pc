#!/usr/bin/env python3
"""Require the continuous held-third-token callback time return."""
import argparse,re
from pathlib import Path
import audit_v1101_postalarm as prefix
from audit_second_irq_output_v1016 import public_line
alarm=prefix.alarm
RESULT=b'V1103_POSTALARM_TIME_RETURN original_return=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 reads=3 offset=1 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
FAULT=rb'V1103_POSTALARM_TIME_FAULT route=[7-9] witness=[0-7] stage=[34]'
TAGS=prefix.TAGS+(b'V1103_',b'V1107_')

def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1103_',b'V1107_'))]
    predecessor=[i for i,l in enumerate(rows) if l.startswith(b'V1095_')]
    ok=False
    if rc==0 and len(hits)==len(predecessor)==1:
        i=hits[0];j=predecessor[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prefix.inspect(b'\n'.join(rows[:i]),0)
    return f'V1107_POSTALARM_TIME_CENSUS verified={int(ok)} original_time_return={int(ok)} token_held={int(ok)} boot_verified=0',ok

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1107_POSTALARM_TIME_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,RESULT,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
