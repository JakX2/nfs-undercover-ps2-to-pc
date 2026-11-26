#!/usr/bin/env python3
"""Require both authenticated ABI admission and actual original third return."""
import argparse,re
from pathlib import Path
import audit_v1041_transfer_abi as abi
import audit_v1031_third_transfer as third
from audit_second_irq_output_v1016 import public_line
old=abi.old
TAGS=abi.TAGS+third.TAGS+(b'V1045_',)
def inspect(raw,rc):
    if len(raw)>old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l.startswith((b'V1028_',b'V1029_',b'V1031_',b'V1045_'))]
    prior=raw;returned=False
    if len(hits)==1:
        i=hits[0];prior=b'\n'.join(rows[:i])
        returned=rows[i]==third.RESULT and not any(l.startswith(TAGS) for l in rows[i+1:])
    line,base=abi.inspect(prior,rc)
    m=re.fullmatch(r'V1041_ABI_CENSUS verified=1 admission=([0-2]) original_transfer_executed=0 boot_verified=0',line)
    admission=int(m[1]) if base and m else 0
    ok=bool(rc==0 and base and admission in (1,2) and returned)
    return f'V1045_THIRD_ABI_CENSUS verified={int(ok)} admission={admission} transfer_return={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1045_THIRD_ABI_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),(old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,old.DETAIL,old.HISTORY,abi.ABI,abi.FAULT,third.DIAG,third.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
