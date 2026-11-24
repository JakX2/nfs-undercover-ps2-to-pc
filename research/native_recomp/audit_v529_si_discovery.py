#!/usr/bin/env python3
import argparse
from audit_v524_si_sampling import diagnostic
from pathlib import Path
from audit_v524_si_sampling import MARKERS as PRIOR,MAX_LOG,inspect as inspect_sample
DISC=b'V529_SI_DISCOVERY_'
MARKERS=PRIOR+(DISC,)
STAGES=[f'V529_SI_DISCOVERY_STAGE n={i}'.encode() for i in range(1,14)]
RESULT=b'V529_SI_DISCOVERY_RESULT type_calls=4 immediate=1 queued=3 completed=1 norep=1 irq=1 sram_entry=1 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(lines) if l.startswith(DISC)),len(lines))
    _,prior=inspect_sample(b'\n'.join(lines[:i]),0);tail=lines[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V529_SI_DISCOVERY_CENSUS rc={rc} sample={int(prior)} stages={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
        diag=diagnostic(raw,a.rc)
    except (OSError,ValueError):
        print('V529_SI_DISCOVERY_AUDIT inspected=0');return 1
    if diag:print(diag)
    print(row);print('V529_SI_DISCOVERY_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
