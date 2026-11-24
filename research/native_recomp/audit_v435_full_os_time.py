#!/usr/bin/env python3
"""Privacy-safe cold OSInit time continuation gate."""
import argparse
from pathlib import Path
import re
from audit_v433_full_os_entry import PREFIX,inspect as inspect_os,MAX_LOG
MARK=b'V435_TIME_'
STAGES=[f'V435_TIME_STAGE n={n} valid=1'.encode() for n in range(1,7)]
RESULT=b'V435_TIME_RESULT frame=1 spills=12 time=1 irq_restored=1 stores=2 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V435_TIME_INVALID reason=([1-8]) stage=([0-6])')

def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX+(MARK,))]
    i=next((i for i,l in enumerate(lines) if l.startswith(MARK)),len(lines))
    _,os_ok=inspect_os(b'\n'.join(lines[:i]),0)
    tail=lines[i:];count=0
    for expected in STAGES:
        if count>=len(tail) or tail[count]!=expected:break
        count+=1
    invalid=[m for l in tail if (m:=INVALID.fullmatch(l))]
    reason=int(invalid[0][1]) if len(invalid)==1 else 0
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    verified=rc==0 and os_ok and tail==STAGES+[RESULT] and not fallback
    return f'V435_TIME_CENSUS rc={rc} os_entry={int(os_ok)} stages={count} fallback={fallback} reason={reason} verified={int(verified)} boot_verified=0',verified

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V435_TIME_AUDIT inspected=0');return 1
    print(row);print('V435_TIME_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
