#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v663_external_entry import MARKERS as PRIOR,MAX_LOG,inspect as inspect_external
PREFIX=b'V667_SI_DISPATCH_'
MARKERS=PRIOR+(PREFIX,)
EVENTS=[f'V667_SI_DISPATCH_STAGE n={i}'.encode() for i in range(1,7)]
RESULT=b'V667_SI_DISPATCH_RESULT pi_reads=1 timebase=1 scheduler_disable=1 handler=1 index=20 si_pending=1 ack=0 rfi_return=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(rows) if l.startswith(PREFIX)),len(rows))
    _,prior=inspect_external(b'\n'.join(rows[:i]),0)
    tail=rows[i:];n=0
    for a,b in zip(tail,EVENTS):
        if a!=b:break
        n+=1
    ok=bool(rc==0 and prior and tail==EVENTS+[RESULT])
    return f'V667_SI_DISPATCH_CENSUS rc={rc} external={int(prior)} stages={n} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V667_SI_DISPATCH_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V667_SI_DISPATCH_INVALID reason=[1-6] stage=[0-6]|V663_EXTERNAL_INVALID reason=[1-9] stage=[0-6]|V663_EXTERNAL_PENDING active=[0-9]{1,10}|V670_VECTOR_REFUSAL mask=[0-9]{1,4}',l):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
