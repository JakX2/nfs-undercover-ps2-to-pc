#!/usr/bin/env python3
"""Certify the original third post-ACK unchanged wireless setter return."""
import argparse
from pathlib import Path
import audit_v1194_ack_frontier as prior_frontier
from audit_second_irq_output_v1016 import public_line
prior_time=prior_frontier.prior_time;prior_prefix=prior_time.prior_prefix;callback=prior_time.callback;helper=prior_time.helper;ack=prior_time.ack;dispatch=prior_time.dispatch;epilogue=prior_time.epilogue;returned=prior_time.returned
handler=prior_time.handler;ret=prior_time.ret;suffix=prior_time.suffix;wireless=prior_time.wireless
frontier=prior_time.frontier;time=prior_time.time;prefix=prior_time.prefix;alarm=prior_time.alarm
RESULT=b'V1197_ACK_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=66 stores=12 token=3 saved_fields=38 pi_cleared=1 continuation_executed=0 boot_verified=0'
DIAG=rb'V1197_ACK_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=[1-9][0-9]{0,2} stores=[0-9][0-9]? token=3 saved_fields=38 pi_cleared=1 continuation_executed=0 boot_verified=0'
FAULT=prior_frontier.FAULT
TAGS=prior_frontier.TAGS+(b'V1197_',b'V1198_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1197_',b'V1198_'))]
    prior=[i for i,l in enumerate(rows) if l==prior_frontier.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prior_frontier.inspect(b'\n'.join(rows[:i]),0)
    return f'V1198_ACK_WIRELESS_CENSUS verified={int(ok)} unchanged_setter={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1198_ACK_WIRELESS_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
