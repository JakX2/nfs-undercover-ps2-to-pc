#!/usr/bin/env python3
"""Certify the final native resume label, before its original instruction."""
import argparse
from pathlib import Path
import audit_v1218_ack_final as prior_final
from audit_second_irq_output_v1016 import public_line
prior_handler_return=prior_final.prior_handler_return;prior_handler=prior_final.prior_handler;prior_return=prior_final.prior_return;prior_suffix=prior_final.prior_suffix;prior_wireless=prior_final.prior_wireless;prior_frontier=prior_final.prior_frontier;prior_time=prior_final.prior_time;prior_prefix=prior_final.prior_prefix;callback=prior_final.callback;helper=prior_final.helper;ack=prior_final.ack;dispatch=prior_final.dispatch;epilogue=prior_final.epilogue;returned=prior_final.returned
handler=prior_final.handler;ret=prior_final.ret;suffix=prior_final.suffix;wireless=prior_final.wireless
frontier=prior_final.frontier;time=prior_final.time;prefix=prior_final.prefix;alarm=prior_final.alarm
RESULT=b'V1220_ACK_FINAL_RESUME original_resume=1 restored_context=1 dispatch_ticks=2 token=3 pi_cleared=1 resumed_instruction_executed=0 boot_verified=0'
DIAG=RESULT
FAULT=prior_final.FAULT
TAGS=prior_final.TAGS+(b'V1220_',b'V1221_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1220_',b'V1221_'))]
    prior=[i for i,l in enumerate(rows) if l==prior_final.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prior_final.inspect(b'\n'.join(rows[:i]),0)
    return f'V1221_ACK_RESUME_CENSUS verified={int(ok)} original_resume={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1221_ACK_RESUME_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,prior_return.DIAG,prior_handler.DIAG,prior_handler_return.DIAG,prior_final.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
