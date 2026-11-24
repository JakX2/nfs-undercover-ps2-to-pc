#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v628_startup_census as prior
MAX_LOG=prior.MAX_LOG
PREFIX=b'V629_STM_'
STAGES=[f'V629_STM_STAGE n={i}'.encode() for i in range(1,4)]
RESULT=re.compile(rb'V629_STM_RESULT entry=1 open=1 pathname=[12] mode=0 native_transport=1 serviced=0 actual_ios=0 fallback=0 boot_verified=0')
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=raw.splitlines();start=next((i for i,l in enumerate(lines) if l.startswith(PREFIX)),len(lines))
    rows=[l for l in lines[start:] if l.startswith(PREFIX)]
    # No predecessor marker may appear again after the STM chain begins.
    foreign=any(l.startswith(prior.ipc.MARKERS) for l in lines[start:])
    earlier,passed=prior.inspect(b'\n'.join(lines[:start]),0 if start<len(lines) else rc)
    n=0
    if passed:
        for a,b in zip(rows,STAGES):
            if a!=b:break
            n+=1
    ok=bool(rc==0 and passed and not foreign and n==3 and len(rows)==4 and RESULT.fullmatch(rows[-1]))
    bad=[l for l in rows if re.fullmatch(rb'V629_STM_INVALID reason=[1-5] stage=[0-3]',l)]
    diag=bad[0].decode() if rc==121 and passed and len(bad)==1 and not foreign else None
    return (*earlier,diag,f'V629_STM_CENSUS rc={rc} ipc={int(passed)} stages={n} verified={int(ok)} boot_verified=0'),ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        rows,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):print('V629_STM_AUDIT inspected=0');return 1
    for row in rows:
        if row:print(row)
    print('V629_STM_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
