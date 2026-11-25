#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v742_handler_time import inspect as time,diagnostic as prior,RESULT as TIME_RESULT,MAX_LOG
from audit_v768_transfer_prefix import ENTRY
PREFIX=(b'V768_TRANSFER_',b'V777_TRANSFER_')
HANDOFF=b'V777_TRANSFER_HANDOFF scheduler_tick=1 ack_identity=1'
RESULT=rb'V777_TRANSFER_RESULT original_return=1 abi=1 irq_restore=1 compiler_restore=1 idle=([01]) irq_lane=([12]) reads=([0-9]{1,2}) writes=([0-9]{1,2}) follow=([023]) pending=([01]) total=([0-9]{1,3}) handler_instruction_executed=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(TIME_RESULT,l)]
    events=[l for l in rows if l.startswith(PREFIX)]
    ok=False;idle=follow=0
    if len(hits)==1 and len(events)==3:
        i=hits[0];_,valid=time(b'\n'.join(rows[:i+1]),0)
        m=re.fullmatch(RESULT,events[2])
        if rc==0 and valid and re.fullmatch(ENTRY,events[0]) and events[1]==HANDOFF and m and not any(l.startswith(PREFIX) for l in rows[:i+1]):
            idle,lane,reads,writes,follow,pending,total=map(int,m.groups())
            ok=bool(events[0].endswith(f'idle={idle}'.encode()) and 2<=total<=512 and reads+writes<=64 and
                    ((idle==0 and reads==writes==follow==pending==0) or
                     (idle==1 and reads>=2 and writes>=3 and follow in (2,3) and pending==int(follow==2))))
    return f'V777_TRANSFER_CENSUS rc={rc} original_return={int(ok)} idle={idle if ok else 0} follow={follow if ok else 0} verified={int(ok)} handler_return=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V777_TRANSFER_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or re.fullmatch(ENTRY,l) or l==HANDOFF or re.fullmatch(RESULT,l) or re.fullmatch(rb'V777_TRANSFER_INVALID kind=[1-7] reason=[0-8] stage=[0-4] visits=[0-9]{1,3} device=[0-7] follow=[0-5] trace=[0-9]{1,2}|V777_TRANSFER_MMIO_INVALID kind=[12] reason=[0-7]',l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
