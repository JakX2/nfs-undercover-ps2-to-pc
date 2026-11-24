#!/usr/bin/env python3
import argparse
from pathlib import Path
from audit_v559_dsp_stage import MARKERS as PRIOR,MAX_LOG,inspect as inspect_stage
SC=b'V574_DSP_SC_'
GATE=b'V572_SC_DIRECT_ONLY'
MARKERS=PRIOR+(SC,GATE)
STAGES=[f'V574_DSP_SC_STAGE n={i}'.encode() for i in range(1,5)]
RESULT=b'V574_DSP_SC_RESULT vector=1 rfi=1 blr=1 staged=128 backup=128 flush=4 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(lines) if l.startswith((SC,GATE))),len(lines))
    _,prior=inspect_stage(b'\n'.join(lines[:i]),0);tail=lines[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V574_DSP_SC_CENSUS rc={rc} staging={int(prior)} stages={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V574_DSP_SC_AUDIT inspected=0');return 1
    print(row);print('V574_DSP_SC_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
