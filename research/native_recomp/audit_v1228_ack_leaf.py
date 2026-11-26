#!/usr/bin/env python3
"""Certify the original IRQ-enable extract, BLR and OSInit caller frontier."""
import argparse
from pathlib import Path
import audit_v1221_ack_resume as prior_resume
from audit_second_irq_output_v1016 import public_line
prior_final=prior_resume.prior_final;prior_handler_return=prior_resume.prior_handler_return;prior_handler=prior_resume.prior_handler;prior_return=prior_resume.prior_return;prior_suffix=prior_resume.prior_suffix;prior_wireless=prior_resume.prior_wireless;prior_frontier=prior_resume.prior_frontier;prior_time=prior_resume.prior_time;prior_prefix=prior_resume.prior_prefix;callback=prior_resume.callback;helper=prior_resume.helper;ack=prior_resume.ack;dispatch=prior_resume.dispatch;epilogue=prior_resume.epilogue;returned=prior_resume.returned
handler=prior_resume.handler;ret=prior_resume.ret;suffix=prior_resume.suffix;wireless=prior_resume.wireless
frontier=prior_resume.frontier;time=prior_resume.time;prefix=prior_resume.prefix;alarm=prior_resume.alarm
RESULT=b'V1227_ACK_LEAF_RETURN original_extract=1 original_blr=1 osinit_resume=1 previous_ee=0 integer_state=1 gqr=1 token=3 pi_cleared=1 caller_instruction_executed=0 boot_verified=0'
DIAG=RESULT
FAULT=prior_resume.FAULT
TAGS=prior_resume.TAGS+(b'V1227_',b'V1228_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1227_',b'V1228_'))]
    prior=[i for i,l in enumerate(rows) if l==prior_resume.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prior_resume.inspect(b'\n'.join(rows[:i]),0)
    return f'V1228_ACK_LEAF_CENSUS verified={int(ok)} osinit_resume={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1228_ACK_LEAF_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,prior_return.DIAG,prior_handler.DIAG,prior_handler_return.DIAG,prior_final.DIAG,prior_resume.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
