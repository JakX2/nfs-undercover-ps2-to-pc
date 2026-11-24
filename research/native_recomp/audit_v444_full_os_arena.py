#!/usr/bin/env python3
"""Audit the complete-image arena continuation without exposing guest data."""
import argparse
from pathlib import Path
import re
from audit_v439_full_os_hardware import PREFIX,MARK,HW,inspect as inspect_hw,MAX_LOG
ARENA=b'V444_ARENA_'
BEGIN=re.compile(rb'V444_ARENA_BEGIN boot_path=([012]) direct_low=([01])')
STAGES=[f'V444_ARENA_STAGE n={i} valid=1'.encode() for i in range(1,4)]
RESULT=b'V444_ARENA_RESULT boot_info=1 low_store=1 high_store=1 bounds=1 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V444_ARENA_INVALID reason=([1-9]) stage=([0-4])')
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX+(MARK,HW,ARENA))]
    i=next((i for i,l in enumerate(lines) if l.startswith(ARENA)),len(lines))
    _,prior=inspect_hw(b'\n'.join(lines[:i]),0);tail=lines[i:]
    begin=BEGIN.fullmatch(tail[0]) if tail else None
    count=0
    if begin:
        for a,b in zip(tail[1:],STAGES):
            if a!=b:break
            count+=1
    errors=[m for l in tail if (m:=INVALID.fullmatch(l))]
    reason=int(errors[0][1]) if len(errors)==1 else 0
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and begin and tail[1:]==STAGES+[RESULT] and not fallback)
    return f'V444_ARENA_CENSUS rc={rc} hardware={int(prior)} stages={count} boot_path={int(begin[1]) if begin else 0} direct_low={int(begin[2]) if begin else 0} fallback={fallback} reason={reason} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V444_ARENA_AUDIT inspected=0');return 1
    print(row);print('V444_ARENA_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
