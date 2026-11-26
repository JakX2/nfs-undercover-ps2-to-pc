#!/usr/bin/env python3
"""Strict original Open request construction with ordered native SC proof."""
import argparse
from pathlib import Path
import audit_v1240_ack_stm as prior_stm
from audit_v1240_ack_stm import prior_complete,prior_ipc,prior_leaf,prior_resume,prior_final,prior_handler_return,prior_handler,prior_return,prior_suffix,prior_wireless,prior_frontier,prior_time,prior_prefix,callback,helper,ack,dispatch,epilogue,returned,handler,ret,suffix,wireless,frontier,time,prefix,alarm
from audit_second_irq_output_v1016 import public_line
RESULTS=tuple(f'V1247_ACK_OPEN_REQUEST allocation=1 cache=1 native_rfi=1 request=1 path={n} token=3 si_quiescent=1 submitted=0 serviced=0 boot_verified=0'.encode() for n in (1,2))
STAGES=tuple(f'V1247_ACK_OPEN_STAGE n={n}'.encode() for n in range(1,10))
VECTOR=b'V1247_ACK_OPEN_VECTOR native_entry=1'
SC_RETURN=b'V1247_ACK_OPEN_SC_RETURN native_rfi=1'
EVENTS=STAGES[:7]+(VECTOR,SC_RETURN)+STAGES[7:]
STAGE=rb'V1247_ACK_OPEN_STAGE n=[1-9]'
FAULT=rb'V1247_ACK_OPEN_INVALID kind=[1-4] stage=[0-9] reason=[0-3] request=[0-6]'
TAGS=prior_stm.TAGS+(b'V1247_',)
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    prior=[(i,prior_stm.RESULTS.index(l)) for i,l in enumerate(rows) if l in prior_stm.RESULTS]
    hits=[i for i,l in enumerate(rows) if l.startswith(b'V1247_')]
    ok=False
    if rc==0 and len(prior)==1 and len(hits)==len(EVENTS)+1:
        j,k=prior[0]
        if j<hits[0] and tuple(l for l in rows[j+1:] if l.startswith(TAGS))==EVENTS+(RESULTS[k],):
            _,ok=prior_stm.inspect(b'\n'.join(rows[:j+1]),0)
    return f'V1247_ACK_OPEN_CENSUS verified={int(ok)} native_rfi={int(ok)} request={int(ok)} submitted=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1247_ACK_OPEN_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,ack.DIAG,helper.DIAG,callback.DIAG,prior_prefix.DIAG,prior_time.DIAG,prior_frontier.DIAG,prior_wireless.DIAG,prior_suffix.DIAG,prior_return.DIAG,prior_handler.DIAG,prior_handler_return.DIAG,prior_final.DIAG,prior_resume.DIAG,prior_leaf.DIAG,prior_ipc.RESULT,prior_ipc.FAULT,prior_complete.RESULT,prior_complete.FAULT,prior_complete.STAGE,*prior_stm.RESULTS,prior_stm.FAULT,prior_stm.STAGE,*RESULTS,FAULT,STAGE,VECTOR,SC_RETURN,prior_leaf.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
