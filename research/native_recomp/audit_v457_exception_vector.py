#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
from audit_v446_full_os_ipc import PREFIX,MARK,HW,ARENA,IPC,MAX_LOG,inspect as inspect_ipc
VECTOR=b'V457_VECTOR_'
BEGIN=re.compile(rb'V457_VECTOR_BEGIN debug_needed=([01])')
STAGES=[f'V457_VECTOR_STAGE n={i} valid=1'.encode() for i in range(1,5)]
RESULT=b'V457_VECTOR_RESULT copied=152 flush=5 invalidate=5 sync=2 isync=1 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V457_VECTOR_INVALID reason=([1-9]|10) stage=([0-4])')
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX+(MARK,HW,ARENA,IPC,VECTOR))]
    i=next((i for i,l in enumerate(lines) if l.startswith(VECTOR)),len(lines))
    _,prior=inspect_ipc(b'\n'.join(lines[:i]),0);tail=lines[i:]
    begin=BEGIN.fullmatch(tail[0]) if tail else None
    prelude=0;count=0
    if begin:
        while prelude<24 and len(tail)>1+prelude and tail[1+prelude]==f'V457_VECTOR_PRELUDE n={prelude+1}'.encode():prelude+=1
        for a,b in zip(tail[1+prelude:],STAGES):
            if a!=b:break
            count+=1
    errors=[m for l in tail if (m:=INVALID.fullmatch(l))]
    reason=int(errors[0][1]) if len(errors)==1 else 0
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and begin and prelude and tail[1+prelude:]==STAGES+[RESULT] and not fallback)
    return f'V457_VECTOR_CENSUS rc={rc} ipc={int(prior)} prelude={prelude} stages={count} debug_needed={int(begin[1]) if begin else 0} fallback={fallback} reason={reason} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V457_VECTOR_AUDIT inspected=0');return 1
    print(row);print('V457_VECTOR_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
