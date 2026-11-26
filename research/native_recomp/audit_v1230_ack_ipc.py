#!/usr/bin/env python3
"""Strict original post-ACK IPC entry; disclose only exact public markers."""
import argparse
from pathlib import Path
import audit_v1228_ack_leaf as prior_leaf
from audit_v1228_ack_leaf import prior_resume,prior_final,prior_handler_return,prior_handler,prior_return,prior_suffix,prior_wireless,prior_frontier,prior_time,prior_prefix,callback,helper,ack,dispatch,epilogue,returned,handler,ret,suffix,wireless,frontier,time,prefix,alarm
from audit_second_irq_output_v1016 import public_line
RESULT=b'V1230_ACK_IPC_ENTRY original_bl=1 original_target=1 cold_prerequisites=1 same_tick=1 token=3 pi_cleared=1 ipc_instruction_executed=0 boot_verified=0'
FAULT=rb'V1230_ACK_IPC_INVALID stage=[0-3] reason=[0-3] cold=[0-7] refusal=[0-9]{1,5} join=[0-2]'
TAGS=prior_leaf.TAGS+(b'V1230_',)
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith(b'V1230_')]
    prior=[i for i,l in enumerate(rows) if l==prior_leaf.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=prior_leaf.inspect(b'\n'.join(rows[:i]),0)
    return f'V1230_ACK_IPC_CENSUS verified={int(ok)} original_entry={int(ok)} cold_prerequisites={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1230_ACK_IPC_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,prior_return.DIAG,prior_handler.DIAG,prior_handler_return.DIAG,prior_final.DIAG,prior_resume.DIAG,prior_leaf.DIAG,RESULT,FAULT,prior_leaf.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
