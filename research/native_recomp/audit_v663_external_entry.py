#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v609_arena_clear import MARKERS as PRIOR,MAX_LOG,inspect as inspect_arena
PREFIX=b'V663_EXTERNAL_'
EVENTS=[f'V663_EXTERNAL_STAGE n={i}'.encode() for i in range(1,7)]
RESULT=b'V663_EXTERNAL_RESULT vector=1 saved_context=1 dispatcher=1 si_pending=1 ack=0 rfi_return=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(PRIOR+(PREFIX,b'V616_IRQ_'))]
    i=next((i for i,l in enumerate(rows) if l.startswith((PREFIX,b'V616_IRQ_'))),len(rows))
    _,prior=inspect_arena(b'\n'.join(rows[:i]),0)
    tail=rows[i:];n=0
    for a,b in zip(tail,EVENTS):
        if a!=b:break
        n+=1
    ok=bool(rc==0 and prior and tail==EVENTS+[RESULT])
    return f'V663_EXTERNAL_CENSUS rc={rc} arena={int(prior)} stages={n} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V663_EXTERNAL_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V663_EXTERNAL_INVALID reason=[1-9] stage=[0-6]|V663_EXTERNAL_PENDING active=[0-9]{1,10}',l):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
