#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v616_irq_enable import MARKERS as PRIOR,MAX_LOG,inspect as inspect_irq
PREFIX=b'V625_IPC_'
MARKERS=PRIOR+(PREFIX,)
STAGES=[f'V625_IPC_STAGE n={n}'.encode() for n in range(1,20)]
RESULT=b'V625_IPC_RESULT calls=17 heap=1 handler=1 mailbox=1 returned=1 queued=0 serviced=0 actual_ios=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(rows) if l.startswith(PREFIX)),len(rows))
    _,prior=inspect_irq(b'\n'.join(rows[:i]),0);tail=rows[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in rows)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V625_IPC_CENSUS rc={rc} irq={int(prior)} stages={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V625_IPC_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V625_IPC_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}|V616_IRQ_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}|V591_MI_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}',l):
            print(l.decode());break
    print(row);print('V625_IPC_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
