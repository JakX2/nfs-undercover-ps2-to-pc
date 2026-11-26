#!/usr/bin/env python3
"""Audit the original third transfer only after the authenticated no-response call."""
import argparse,re
from pathlib import Path
import audit_v1021_error_frontier as old
from audit_second_irq_output_v1016 import public_line
# All 16 V1022 original queued cases: 105 visits, two reads, three writes.
RESULT=b'V1028_THIRD_RETURN original_transfer=1 token=3 pending=0 visits=105 entries=5 returns=5 reads=2 writes=3 saved_fields=38 handler_instruction_executed=0 boot_verified=0'
DIAG=rb'V1028_THIRD_RETURN original_transfer=1 token=3 pending=[01] visits=[0-9]{1,4} entries=[0-9]{1,3} returns=[0-9]{1,3} reads=[0-9]{1,3} writes=[0-9]{1,3} saved_fields=38 handler_instruction_executed=0 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=17 stage=[0-5] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
TAGS=old.TAGS+(b'V1028_',b'V1029_',b'V1031_')
def inspect(raw,rc):
    if len(raw)>old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l.startswith((b'V1028_',b'V1029_',b'V1031_'))]
    prior=raw;done=0;shape=True
    if hits:
        i=hits[0];prior=b'\n'.join(rows[:i])
        shape=len(hits)==1 and rows[i]==RESULT and not any(l.startswith(TAGS) for l in rows[i+1:])
        done=int(shape)
    line,ok=old.inspect(prior,rc)
    # The alternate legitimate callback frontier is classified but does
    # not count as a native third transfer.
    direct='branch=4 admitted=1' in line
    ok=bool(ok and shape and (direct==bool(done)))
    return f'V1031_THIRD_CENSUS verified={int(ok)} transfer_return={done if ok else 0} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1031_THIRD_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),(old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,DIAG,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
