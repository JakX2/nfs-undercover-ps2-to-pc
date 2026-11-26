#!/usr/bin/env python3
"""Strict post-ACK IPC client return census."""
import argparse
from pathlib import Path
import audit_v1230_ack_ipc as prior_ipc
from audit_v1230_ack_ipc import prior_leaf,prior_resume,prior_final,prior_handler_return,prior_handler,prior_return,prior_suffix,prior_wireless,prior_frontier,prior_time,prior_prefix,callback,helper,ack,dispatch,epilogue,returned,handler,ret,suffix,wireless,frontier,time,prefix,alarm
from audit_second_irq_output_v1016 import public_line
RESULT=b'V1235_ACK_IPC_RETURN calls=17 heap=1 handler=1 mailbox=1 returned=1 token=3 si_quiescent=1 queued=0 serviced=0 actual_ios=0 boot_verified=0'
STAGES=tuple(f'V1235_ACK_IPC_STAGE n={n}'.encode() for n in range(3,20))
STAGE=rb'V1235_ACK_IPC_STAGE n=([3-9]|1[0-9])'
FAULT=rb'V1235_ACK_IPC_INVALID kind=[1-3] stage=[3-5] client=([2-9]|1[0-9]) reason=[0-4] cold=[0-7]'
TAGS=prior_ipc.TAGS+(b'V1235_',)
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    prior=[i for i,l in enumerate(rows) if l==prior_ipc.RESULT]
    hits=[i for i,l in enumerate(rows) if l.startswith(b'V1235_')]
    ok=False
    if rc==0 and len(prior)==1 and len(hits)==len(STAGES)+1:
        j=prior[0]
        if j<hits[0] and tuple(l for l in rows[j+1:] if l.startswith(TAGS))==STAGES+(RESULT,):
            _,ok=prior_ipc.inspect(b'\n'.join(rows[:j+1]),0)
    return f'V1235_ACK_IPC_COMPLETE_CENSUS verified={int(ok)} original_return={int(ok)} si_quiescent={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1235_ACK_IPC_COMPLETE_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,prior_return.DIAG,prior_handler.DIAG,prior_handler_return.DIAG,prior_final.DIAG,prior_resume.DIAG,prior_leaf.DIAG,prior_ipc.RESULT,prior_ipc.FAULT,RESULT,FAULT,STAGE,prior_leaf.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
