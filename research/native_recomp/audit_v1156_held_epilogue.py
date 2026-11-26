#!/usr/bin/env python3
"""Certify held third-token RFI and the original fresh dispatcher entry."""
import argparse
from pathlib import Path
import audit_v1148_postalarm_handler_return as returned
handler=returned.handler
ret=handler.ret
suffix=ret.suffix
wireless=suffix.wireless
frontier=wireless.frontier
from audit_second_irq_output_v1016 import public_line
time=frontier.time;prefix=time.prefix;alarm=prefix.alarm
RFI=b'V1151_HELD_PENDING_RFI native_rfi=1 pending_exception=1 visits=82 token=3 held=1 resumed_instruction_executed=0 boot_verified=0'
RESULT=b'V1151_HELD_VECTOR_JOIN original_vector=1 original_trampoline=1 saved_fields=38 vector_visits=34 trampoline_visits=20 token=3 held=1 dispatcher_instruction_executed=0 boot_verified=0'
RFI_DIAG=rb'V1151_HELD_PENDING_RFI native_rfi=1 pending_exception=1 visits=[1-9][0-9]{0,2} token=3 held=1 resumed_instruction_executed=0 boot_verified=0'
DIAG=rb'V1151_HELD_VECTOR_JOIN original_vector=1 original_trampoline=1 saved_fields=38 vector_visits=[1-9][0-9]{0,2} trampoline_visits=[1-9][0-9]{0,2} token=3 held=1 dispatcher_instruction_executed=0 boot_verified=0'
FAULT=rb'V1151_HELD_EPILOGUE_FAULT stage=[0-5] reason=[0-5] epilogue=[0-9] reentry=[0-9]{1,2}'
TAGS=returned.TAGS+(b'V1151_',b'V1156_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1151_',b'V1156_'))]
    prior=[i for i,l in enumerate(rows) if l.startswith(b'V1145_')]
    ok=False
    if rc==0 and len(hits)==2 and len(prior)==1:
        i,k=hits;j=prior[0]
        if j<i<k and rows[i]==RFI and rows[k]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:k]+rows[k+1:]):
            _,ok=returned.inspect(b'\n'.join(rows[:i]),0)
    return f'V1156_HELD_EPILOGUE_CENSUS verified={int(ok)} original_rfi={int(ok)} third_vector={int(ok)} token_held={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1156_HELD_EPILOGUE_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,RFI_DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
