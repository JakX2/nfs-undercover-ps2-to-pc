#!/usr/bin/env python3
"""Certify the original third post-ACK compiler restore frontier."""
import argparse
from pathlib import Path
import audit_v1198_ack_wireless as prior_wireless
from audit_second_irq_output_v1016 import public_line
prior_frontier=prior_wireless.prior_frontier;prior_time=prior_wireless.prior_time;prior_prefix=prior_wireless.prior_prefix;callback=prior_wireless.callback;helper=prior_wireless.helper;ack=prior_wireless.ack;dispatch=prior_wireless.dispatch;epilogue=prior_wireless.epilogue;returned=prior_wireless.returned
handler=prior_wireless.handler;ret=prior_wireless.ret;suffix=prior_wireless.suffix;wireless=prior_wireless.wireless
frontier=prior_wireless.frontier;time=prior_wireless.time;prefix=prior_wireless.prefix;alarm=prior_wireless.alarm
RESULT=b'V1201_ACK_CALLBACK_SUFFIX ordinal=13 target_class=0 visits=37 writes=0 polls=4 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0'
DIAG=rb'V1201_ACK_CALLBACK_SUFFIX ordinal=(4|13) target_class=[012] visits=[1-9][0-9]{0,2} writes=[0-9][0-9]? polls=[0-9][0-9]? token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0'
FAULT=prior_wireless.FAULT
TAGS=prior_wireless.TAGS+(b'V1201_',b'V1203_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1201_',b'V1203_'))]
    prior=[i for i,l in enumerate(rows) if l==prior_wireless.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prior_wireless.inspect(b'\n'.join(rows[:i]),0)
    return f'V1203_ACK_SUFFIX_CENSUS verified={int(ok)} restore_frontier={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1203_ACK_SUFFIX_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
