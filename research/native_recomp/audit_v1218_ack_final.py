#!/usr/bin/env python3
"""Certify final cleared-PI original RFI and both polls."""
import argparse
from pathlib import Path
import audit_v1215_ack_handler_return as prior_handler_return
from audit_second_irq_output_v1016 import public_line
prior_handler=prior_handler_return.prior_handler;prior_return=prior_handler.prior_return;prior_suffix=prior_handler.prior_suffix;prior_wireless=prior_handler.prior_wireless;prior_frontier=prior_handler.prior_frontier;prior_time=prior_handler.prior_time;prior_prefix=prior_handler.prior_prefix;callback=prior_handler.callback;helper=prior_handler.helper;ack=prior_handler.ack;dispatch=prior_handler.dispatch;epilogue=prior_handler.epilogue;returned=prior_handler.returned
handler=prior_handler.handler;ret=prior_handler.ret;suffix=prior_handler.suffix;wireless=prior_handler.wireless
frontier=prior_handler.frontier;time=prior_handler.time;prefix=prior_handler.prefix;alarm=prior_handler.alarm
RESULT=b'V1217_ACK_FINAL_RFI native_rfi=1 restored_context=1 visits=82 polls=2 token=3 pi_cleared=1 resumed_instruction_executed=0 boot_verified=0'
DIAG=rb'V1217_ACK_FINAL_RFI native_rfi=1 restored_context=1 visits=[1-9][0-9]{0,2} polls=2 token=3 pi_cleared=1 resumed_instruction_executed=0 boot_verified=0'
FAULT=prior_handler_return.FAULT
TAGS=prior_handler_return.TAGS+(b'V1217_',b'V1218_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1217_',b'V1218_'))]
    prior=[i for i,l in enumerate(rows) if l==prior_handler_return.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prior_handler_return.inspect(b'\n'.join(rows[:i]),0)
    return f'V1218_ACK_FINAL_CENSUS verified={int(ok)} native_rfi={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1218_ACK_FINAL_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,prior_return.DIAG,prior_handler.DIAG,prior_handler_return.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
