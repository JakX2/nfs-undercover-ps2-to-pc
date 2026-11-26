#!/usr/bin/env python3
"""Require actual third-transfer return and the observed exact original alarm return."""
import argparse,re
from pathlib import Path
import audit_v1045_third_transfer_abi as third
from audit_second_irq_output_v1016 import public_line
abi=third.abi;old=abi.old
TAGS=third.TAGS+(b'V1048_',b'V1054_')
RESULT=rb'V1048_THIRD_ALARM_RETURN original_return=1 queue=1 token=3 lane=0 timer=0 calls=3 visits=33 suffix_visits=6 status_reads=0 status_writes=0 token_held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0'
DIAG=rb'V1048_THIRD_ALARM_RETURN original_return=1 queue=1 token=3 lane=[0-4] timer=[01] calls=[0-9]{1,3} visits=[0-9]{1,4} suffix_visits=[0-9]{1,3} status_reads=[01] status_writes=[01] token_held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0'
FAULT=rb'V1048_THIRD_ALARM_FAULT route=[0-9]{1,2} alarm=[0-9]{1,2} queue=[0-9]{1,2} stage=[0-3]'
HANDOFF=rb'V1087_ALARM_HANDOFF started=[01] first=[01] stage=[0-3] reason=[0-6]'
SEAM=rb'V1087_ALARM_SEAM kind=[12] stage=[0-3] reason=[0-6]'
ACKFAULT=rb'V958_ACK_INVALID kind=19 stage=[0-5] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
def inspect(raw,rc):
    if len(raw)>old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l.startswith((b'V1048_',b'V1054_'))]
    ok=False
    if rc==0 and len(hits)==1:
        i=hits[0];m=re.fullmatch(RESULT,rows[i])
        if m and not any(l.startswith(TAGS) for l in rows[i+1:]):
            prior,base=third.inspect(b'\n'.join(rows[:i]),rc)
            ok=bool(base and 'transfer_return=1' in prior)
    return f'V1054_ALARM_CENSUS verified={int(ok)} original_alarm_return={int(ok)} token_held={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1054_ALARM_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),(old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,DIAG,FAULT,ACKFAULT,HANDOFF,SEAM)):
            print(l.decode())
    print(f'V1087_ALARM_EXIT native_rc={a.rc} audit_passed={int(ok)}')
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
