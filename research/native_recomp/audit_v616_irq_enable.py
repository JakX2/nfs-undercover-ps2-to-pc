#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v609_arena_clear import MARKERS as PRIOR,MAX_LOG,inspect as inspect_arena
PREFIX=b'V616_IRQ_'
MARKERS=PRIOR+(PREFIX,)
EVENTS=[f'V616_IRQ_STAGE n={i}'.encode() for i in range(1,5)]
RESULT=b'V616_IRQ_RESULT returned=1 ee=1 previous=0 ticks=5 pending=0 actual_irq=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(rows) if l.startswith(PREFIX)),len(rows))
    _,prior=inspect_arena(b'\n'.join(rows[:i]),0);tail=rows[i:]
    n=0
    for a,b in zip(tail,EVENTS):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in rows)
    ok=bool(rc==0 and prior and tail==EVENTS+[RESULT] and not fallback)
    return f'V616_IRQ_CENSUS rc={rc} arena={int(prior)} stages={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V616_IRQ_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V616_IRQ_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}|V609_ARENA_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}|V603_REPORT_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2} reports=[0-9]{1,2} getters=[0-9]{1,2}|V591_MI_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}',l):
            print(l.decode());break
    print(row);print('V616_IRQ_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
