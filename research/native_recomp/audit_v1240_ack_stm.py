#!/usr/bin/env python3
"""Strict original STM prefix following a completed IPC return."""
import argparse
from pathlib import Path
import audit_v1235_ack_ipc_complete as prior_complete
from audit_v1235_ack_ipc_complete import prior_ipc,prior_leaf,prior_resume,prior_final,prior_handler_return,prior_handler,prior_return,prior_suffix,prior_wireless,prior_frontier,prior_time,prior_prefix,callback,helper,ack,dispatch,epilogue,returned,handler,ret,suffix,wireless,frontier,time,prefix,alarm
from audit_second_irq_output_v1016 import public_line
RESULTS=tuple(f'V1240_ACK_STM_OPEN original_bridge=1 original_stm=1 original_open_entry=1 path={n} mode=0 token=3 si_quiescent=1 serviced=0 open_instruction_executed=0 boot_verified=0'.encode() for n in (1,2))
STAGES=tuple(f'V1240_ACK_STM_STAGE n={n}'.encode() for n in range(1,4))
STAGE=rb'V1240_ACK_STM_STAGE n=[1-3]'
FAULT=rb'V1240_ACK_STM_INVALID kind=[1-3] stage=[0-3] reason=[0-2] stm=[0-5]'
TAGS=prior_complete.TAGS+(b'V1240_',)
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    prior=[i for i,l in enumerate(rows) if l==prior_complete.RESULT]
    hits=[i for i,l in enumerate(rows) if l.startswith(b'V1240_')]
    ok=False
    if rc==0 and len(prior)==1 and len(hits)==4:
        j=prior[0]
        if j<hits[0] and tuple(l for l in rows[j+1:] if l.startswith(TAGS)) in tuple(STAGES+(r,) for r in RESULTS):
            _,ok=prior_complete.inspect(b'\n'.join(rows[:j+1]),0)
    return f'V1240_ACK_STM_CENSUS verified={int(ok)} original_open_entry={int(ok)} si_quiescent={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1240_ACK_STM_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,prior_return.DIAG,prior_handler.DIAG,prior_handler_return.DIAG,prior_final.DIAG,prior_resume.DIAG,prior_leaf.DIAG,prior_ipc.RESULT,prior_ipc.FAULT,prior_complete.RESULT,prior_complete.FAULT,prior_complete.STAGE,*RESULTS,FAULT,STAGE,prior_leaf.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
