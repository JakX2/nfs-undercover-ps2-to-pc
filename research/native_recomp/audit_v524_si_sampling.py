#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
from audit_v520_si_entry import MARKERS as PRIOR,MAX_LOG,inspect as inspect_entry
SAMPLE=b'V524_SI_SAMPLE_'
MARKERS=PRIOR+(SAMPLE,)
INVALID=re.compile(rb'V524_SI_SAMPLE_INVALID reason=([1-8]) stage=([0-5]) detail=([0-9]{1,3})')
def diagnostic(raw,rc):
    if len(raw)>MAX_LOG or rc!=106:return None
    rows=[INVALID.fullmatch(l) for l in raw.splitlines() if l.startswith(b'V524_SI_SAMPLE_INVALID ')]
    if len(rows)!=1 or rows[0] is None:return None
    reason,stage,detail=map(int,rows[0].groups())
    if detail>255 or (detail!=0)!=(reason==6 and stage==5):return None
    return f'V543_SI_SAMPLE_DIAG reason={reason} stage={stage} detail={detail} boot_verified=0'
STAGES=[f'V524_SI_SAMPLE_STAGE n={i}'.encode() for i in range(1,7)]
RESULT=b'V524_SI_SAMPLE_RESULT vi=1 poll=1 clear=1 irq=1 type_entry=1 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(lines) if l.startswith(SAMPLE)),len(lines))
    _,prior=inspect_entry(b'\n'.join(lines[:i]),0);tail=lines[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V524_SI_SAMPLE_CENSUS rc={rc} entry={int(prior)} stages={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
        diag=diagnostic(raw,a.rc)
    except (OSError,ValueError):
        print('V524_SI_SAMPLE_AUDIT inspected=0');return 1
    if diag:print(diag)
    print(row);print('V524_SI_SAMPLE_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
