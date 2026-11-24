#!/usr/bin/env python3
"""Emit bounded whole-image cache progress, never raw guest logs."""
import argparse
from pathlib import Path
import re
from audit_v425_full_hardware import STAGES as HARDWARE,MAX_LOG
STAGES=HARDWARE+[f'V428_CACHE_STAGE n={i} valid=1'.encode() for i in range(1,5)]
RESULT=b'V428_CACHE_RESULT cache=1 handler=1 data_entry=1 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V428_CACHE_INVALID reason=([1-5]) stage=([0-4]) calls=([0-9]{1,3})')

def inspect(raw:bytes,rc:int):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith((b'V425_HARDWARE_',b'V428_CACHE_'))]
    n=0
    for expected in STAGES:
        if n>=len(lines) or lines[n]!=expected:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    failures=[m for l in lines if (m:=INVALID.fullmatch(l))]
    reason=int(failures[0][1]) if len(failures)==1 else 0
    calls=int(failures[0][3]) if len(failures)==1 else 0
    malformed=int(any(l not in STAGES+[RESULT,b'V425_HARDWARE_FALLBACK hit=1'] and not INVALID.fullmatch(l) and not re.fullmatch(rb'V425_HARDWARE_INVALID stage=[0-9]',l) for l in lines) or len(failures)>1 or calls>129)
    verified=rc==0 and lines==STAGES+[RESULT]
    return f'V428_CACHE_CENSUS rc={rc} hardware={min(n,9)} cache={max(n-9,0)} fallback={fallback} reason={reason} calls={calls} malformed={malformed} verified={int(verified)} boot_verified=0',verified

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V428_CACHE_AUDIT inspected=0');return 1
    print(row);print('V428_CACHE_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
