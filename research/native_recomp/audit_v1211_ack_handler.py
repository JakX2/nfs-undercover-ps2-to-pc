#!/usr/bin/env python3
"""Certify the original third post-ACK handler status and restore frontier."""
import argparse
from pathlib import Path
import audit_v1207_ack_return as prior_return
from audit_second_irq_output_v1016 import public_line
prior_suffix=prior_return.prior_suffix;prior_wireless=prior_return.prior_wireless;prior_frontier=prior_return.prior_frontier;prior_time=prior_return.prior_time;prior_prefix=prior_return.prior_prefix;callback=prior_return.callback;helper=prior_return.helper;ack=prior_return.ack;dispatch=prior_return.dispatch;epilogue=prior_return.epilogue;returned=prior_return.returned
handler=prior_return.handler;ret=prior_return.ret;suffix=prior_return.suffix;wireless=prior_return.wireless
frontier=prior_return.frontier;time=prior_return.time;prefix=prior_return.prefix;alarm=prior_return.alarm
RESULT=b'V1210_ACK_HANDLER ordinal=12 branch_taken=1 visits=20 stores=0 status_reads=1 status_writes=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0'
DIAG=rb'V1210_ACK_HANDLER ordinal=(7|8|12) branch_taken=[01] visits=[1-9][0-9]{0,2} stores=[0-9][0-9]? status_reads=1 status_writes=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0'
FAULT=prior_return.FAULT
TAGS=prior_return.TAGS+(b'V1210_',b'V1211_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1210_',b'V1211_'))]
    prior=[i for i,l in enumerate(rows) if l==prior_return.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prior_return.inspect(b'\n'.join(rows[:i]),0)
    return f'V1211_ACK_HANDLER_CENSUS verified={int(ok)} original_status={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1211_ACK_HANDLER_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,prior_return.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
