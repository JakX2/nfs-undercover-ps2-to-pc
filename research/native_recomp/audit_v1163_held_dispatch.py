#!/usr/bin/env python3
"""Certify the original fresh third dispatcher through the SI handler boundary."""
import argparse
from pathlib import Path
import audit_v1156_held_epilogue as epilogue
returned=epilogue.returned
handler=returned.handler
ret=handler.ret
suffix=ret.suffix
wireless=suffix.wireless
frontier=wireless.frontier
from audit_second_irq_output_v1016 import public_line
time=frontier.time;prefix=time.prefix;alarm=prefix.alarm
RESULT=b'V1158_HELD_DISPATCH original_dispatcher=1 original_leaves=4 original_indirect=1 visits=153 entries=5 pi_reads=2 polls=10 token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0'
DIAG=rb'V1158_HELD_DISPATCH original_dispatcher=1 original_leaves=4 original_indirect=1 visits=[1-9][0-9]{0,3} entries=5 pi_reads=2 polls=[0-9]{1,3} token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0'
FAULT=rb'V1151_HELD_EPILOGUE_FAULT stage=[0-7] reason=[0-8] epilogue=[0-9] reentry=[0-9]{1,2}'
TAGS=epilogue.TAGS+(b'V1158_',b'V1163_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1158_',b'V1163_'))]
    prior=[i for i,l in enumerate(rows) if l==epilogue.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=epilogue.inspect(b'\n'.join(rows[:i]),0)
    return f'V1163_HELD_DISPATCH_CENSUS verified={int(ok)} original_dispatcher={int(ok)} third_handler={int(ok)} token_held={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1163_HELD_DISPATCH_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
