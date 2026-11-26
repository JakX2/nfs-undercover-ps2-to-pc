#!/usr/bin/env python3
"""Certify the original third post-ACK callback register restoration and return."""
import argparse
from pathlib import Path
import audit_v1203_ack_suffix as prior_suffix
from audit_second_irq_output_v1016 import public_line
prior_wireless=prior_suffix.prior_wireless;prior_frontier=prior_suffix.prior_frontier;prior_time=prior_suffix.prior_time;prior_prefix=prior_suffix.prior_prefix;callback=prior_suffix.callback;helper=prior_suffix.helper;ack=prior_suffix.ack;dispatch=prior_suffix.dispatch;epilogue=prior_suffix.epilogue;returned=prior_suffix.returned
handler=prior_suffix.handler;ret=prior_suffix.ret;suffix=prior_suffix.suffix;wireless=prior_suffix.wireless
frontier=prior_suffix.frontier;time=prior_suffix.time;prefix=prior_suffix.prefix;alarm=prior_suffix.alarm
RESULT=b'V1205_ACK_CALLBACK_RETURN original_restore=1 original_return=1 visits=12 token=3 saved_fields=38 pi_cleared=1 handler_instruction_executed=0 boot_verified=0'
DIAG=rb'V1205_ACK_CALLBACK_RETURN original_restore=1 original_return=1 visits=[1-9][0-9]{0,2} token=3 saved_fields=38 pi_cleared=1 handler_instruction_executed=0 boot_verified=0'
FAULT=prior_suffix.FAULT
TAGS=prior_suffix.TAGS+(b'V1205_',b'V1207_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1205_',b'V1207_'))]
    prior=[i for i,l in enumerate(rows) if l==prior_suffix.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prior_suffix.inspect(b'\n'.join(rows[:i]),0)
    return f'V1207_ACK_RETURN_CENSUS verified={int(ok)} original_callback_return={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1207_ACK_RETURN_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
