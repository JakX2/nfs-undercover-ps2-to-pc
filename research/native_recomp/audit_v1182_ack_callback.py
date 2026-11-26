#!/usr/bin/env python3
"""Certify the original third post-ACK alternate callback frontier."""
import argparse,re
from pathlib import Path
import audit_v1177_ack_helper as helper
from audit_second_irq_output_v1016 import public_line
ack=helper.ack;dispatch=helper.dispatch;epilogue=helper.epilogue;returned=helper.returned
handler=helper.handler;ret=helper.ret;suffix=helper.suffix;wireless=helper.wireless
frontier=helper.frontier;time=helper.time;prefix=helper.prefix;alarm=helper.alarm
RESULT=b'V1180_ACK_CALLBACK_FRONTIER target_class=2 aligned=1 visits=71 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0'
DIAG=rb'V1180_ACK_CALLBACK_FRONTIER target_class=2 aligned=1 visits=([1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-6])(?: path_verified=1(?: nested_calls=4 nested_msr=2)?)? token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0'
PATH_RESULT=DIAG.replace(b'(?: path_verified=1(?: nested_calls=4 nested_msr=2)?)?',b' path_verified=1(?: nested_calls=4 nested_msr=2)?')
def is_result(row):return row==RESULT or re.fullmatch(PATH_RESULT,row) is not None
FAULT=helper.FAULT
REFUSAL=rb'V1263_ACK_CALLBACK_REFUSAL kind=([1-9]|1[01]) visits=[0-9]{1,4} expected=[0-9]{1,4} identity=[0-4]'
TAGS=helper.TAGS+(b'V1180_',b'V1182_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1180_',b'V1182_'))]
    prior=[i for i,l in enumerate(rows) if l==helper.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and is_result(rows[i]) and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=helper.inspect(b'\n'.join(rows[:i]),0)
    return f'V1182_ACK_CALLBACK_CENSUS verified={int(ok)} callback_frontier={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1182_ACK_CALLBACK_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,DIAG,FAULT,REFUSAL)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
