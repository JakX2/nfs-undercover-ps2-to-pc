#!/usr/bin/env python3
"""Certify a held-token callback prefix only after the continuous third alarm."""
import argparse,re
from pathlib import Path
import audit_v1054_third_alarm as alarm
from audit_second_irq_output_v1016 import public_line

HANDOFF=b'V1087_ALARM_HANDOFF started=1 first=1 stage=1 reason=0'
RESULT=rb'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=([1-9][0-9]{0,2}) visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
FAULT=rb'V1095_AFTER_ALARM_FAULT route=[0-6] prefix=[0-4] stage=[0-3]'
TAGS=alarm.TAGS+(b'V1087_',b'V1095_',b'V1101_')

def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    terminal=[i for i,l in enumerate(rows) if l.startswith((b'V1095_',b'V1101_'))]
    seam=[i for i,l in enumerate(rows) if l.startswith(b'V1087_')]
    returns=[i for i,l in enumerate(rows) if l.startswith(b'V1048_')]
    transfers=[i for i,l in enumerate(rows) if l.startswith(b'V1028_')]
    ok=False
    if rc==0 and len(terminal)==len(seam)==len(returns)==len(transfers)==1:
        end=terminal[0];h=seam[0];a=returns[0];t=transfers[0]
        m=re.fullmatch(RESULT,rows[end])
        if m and int(m[1])<=256 and t<h<a<end and rows[h]==HANDOFF and \
           not any(l.startswith(TAGS) for l in rows[a+1:end]+rows[end+1:]):
            _,ok=alarm.inspect(b'\n'.join(rows[:end]),0)
    return f'V1101_POSTALARM_CENSUS verified={int(ok)} original_callback_prefix={int(ok)} token_held={int(ok)} boot_verified=0',ok

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1101_POSTALARM_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,RESULT,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
