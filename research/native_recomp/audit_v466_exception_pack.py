#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
from audit_v457_exception_vector import PREFIX,MARK,HW,ARENA,IPC,VECTOR,MAX_LOG,inspect as inspect_vector
PACK=b'V466_PACK_'
STAGES=[f'V466_PACK_VECTOR n={i}'.encode() for i in range(1,16)]+[b'V466_PACK_PHASE n=3',b'V466_PACK_PHASE n=4']
RESULT=b'V466_PACK_RESULT vectors=15 syscall=1 alarm_entry=1 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V466_PACK_INVALID reason=([1-9]|1[0-7]) phase=([0-4])')
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX+(MARK,HW,ARENA,IPC,VECTOR,PACK))]
    i=next((i for i,l in enumerate(lines) if l.startswith(PACK)),len(lines))
    _,prior=inspect_vector(b'\n'.join(lines[:i]),0);tail=lines[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    errors=[m for l in tail if (m:=INVALID.fullmatch(l))]
    reason=int(errors[0][1]) if len(errors)==1 else 0
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V466_PACK_CENSUS rc={rc} first_vector={int(prior)} vectors={min(n,15)} syscall={int(n>=16)} alarm={int(n>=17)} fallback={fallback} reason={reason} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V466_PACK_AUDIT inspected=0');return 1
    print(row);print('V466_PACK_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
