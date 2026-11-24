#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v629_stm_open as prior
MAX_LOG=prior.MAX_LOG
PREFIX=b'V641_OPEN_'
EVENTS=[f'V641_OPEN_STAGE n={i}'.encode() for i in range(1,8)]+[b'V641_OPEN_VECTOR entered=1',b'V641_OPEN_RFI returned=1',b'V641_OPEN_STAGE n=8',b'V641_OPEN_STAGE n=9']
RESULT=b'V641_OPEN_RESULT allocation=1 irq_restore=1 flush=1 vector=1 request=1 submitted=0 serviced=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=raw.splitlines();at=next((i for i,l in enumerate(lines) if l.startswith(PREFIX)),len(lines))
    before,passed=prior.inspect(b'\n'.join(lines[:at]),0 if at<len(lines) else rc)
    tail=[l for l in lines[at:] if l.startswith(PREFIX)]
    foreign=any(l.startswith(prior.prior.ipc.MARKERS+(prior.PREFIX,)) for l in lines[at:])
    n=0
    if passed and not foreign:
        for a,b in zip(tail,EVENTS):
            if a!=b:break
            n+=1
    ok=bool(rc==0 and passed and not foreign and tail==EVENTS+[RESULT])
    bad=[l for l in tail if re.fullmatch(rb'V641_OPEN_INVALID reason=[1-6] stage=[0-9]|V641_OPEN_SC_INVALID rejected=1',l)]
    diag=bad[0].decode() if rc==122 and passed and not foreign and len(bad)==1 else None
    return (*before,diag,f'V641_OPEN_CENSUS rc={rc} stm={int(passed)} events={n}/{len(EVENTS)} verified={int(ok)} boot_verified=0'),ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        rows,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):print('V641_OPEN_AUDIT inspected=0');return 1
    for row in rows:
        if row:print(row)
    print('V641_OPEN_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
