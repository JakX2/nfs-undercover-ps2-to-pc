#!/usr/bin/env python3
"""Certify the third original SI completion ACK before its successor executes."""
import argparse
from pathlib import Path
import audit_v1163_held_dispatch as dispatch
epilogue=dispatch.epilogue
returned=epilogue.returned
handler=returned.handler
ret=handler.ret
suffix=ret.suffix
wireless=suffix.wireless
frontier=wireless.frontier
from audit_second_irq_output_v1016 import public_line
time=frontier.time;prefix=time.prefix;alarm=prefix.alarm
RESULT=b'V1167_THIRD_ACK original_w1c=1 next_label=1 token=3 no_response=1 visits=48 entries=2 returns=1 reads=3 writes=1 saved_fields=38 retired_transfer=1 pi_cleared=1 successor_executed=0 boot_verified=0'
DIAG=rb'V1167_THIRD_ACK original_w1c=1 next_label=1 token=3 no_response=[01] visits=[1-9][0-9]{0,3} entries=[0-9]{1,2} returns=[0-9]{1,2} reads=[0-9]{1,3} writes=[0-9]{1,3} saved_fields=38 retired_transfer=1 pi_cleared=1 successor_executed=0 boot_verified=0'
FAULT=rb'V1151_HELD_EPILOGUE_FAULT stage=[0-9] reason=[0-9]{1,2} epilogue=[0-9] reentry=[0-9]{1,2}'
TAGS=dispatch.TAGS+(b'V1167_',b'V1171_')
def inspect(raw,rc):
    if len(raw)>alarm.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1167_',b'V1171_'))]
    prior=[i for i,l in enumerate(rows) if l==dispatch.RESULT]
    ok=False
    if rc==0 and len(hits)==len(prior)==1:
        i=hits[0];j=prior[0]
        if j<i and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[j+1:i]+rows[i+1:]):
            _,ok=dispatch.inspect(b'\n'.join(rows[:i]),0)
    return f'V1171_THIRD_ACK_CENSUS verified={int(ok)} original_ack={int(ok)} retired_transfer={int(ok)} pi_cleared={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>alarm.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V1171_THIRD_ACK_AUDIT inspected=0');return 1
    old=alarm.old;abi=alarm.abi;third=alarm.third
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),
            (old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,
             old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,
             old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.third.DIAG,third.third.FAULT,
             alarm.DIAG,alarm.FAULT,alarm.ACKFAULT,alarm.HANDOFF,alarm.SEAM,prefix.RESULT,prefix.FAULT,
             time.RESULT,time.FAULT,frontier.DIAG,frontier.FAULT,wireless.DIAG,wireless.FAULT,suffix.DIAG,suffix.FAULT,ret.DIAG,ret.FAULT,handler.DIAG,handler.FAULT,returned.DIAG,returned.FAULT,epilogue.RFI_DIAG,epilogue.DIAG,dispatch.DIAG,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
