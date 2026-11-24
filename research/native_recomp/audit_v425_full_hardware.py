#!/usr/bin/env python3
"""Allowlist the full-image hardware witness; never emit raw guest logs."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
MAX_LOG=8*1024*1024
STAGES=[f'V425_HARDWARE_STAGE n={i} valid=1'.encode() for i in range(1,10)]
RESULT=b'V425_HARDWARE_RESULT entry=1 registers=1 ps=1 fpr=1 cache_entry=1 fallback=0 boot_verified=0'
MARKERS=(b'V425_HARDWARE_STAGE',b'V425_HARDWARE_RESULT',b'V425_HARDWARE_INVALID',b'V425_HARDWARE_FALLBACK')

def inspect(raw:bytes,rc:int)->tuple[str,bool]:
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('log geometry')
    lines=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    n=0
    for stage in STAGES:
        if n>=len(lines) or lines[n]!=stage:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    malformed=int(any(l not in STAGES+[RESULT,b'V425_HARDWARE_FALLBACK hit=1'] and not re.fullmatch(rb'V425_HARDWARE_INVALID stage=[0-9]',l) for l in lines))
    verified=rc==0 and lines==STAGES+[RESULT]
    kind='zero' if rc==0 else 'timeout' if rc in (124,137) else 'signal' if rc>=128 else 'nonzero'
    return f'V425_HARDWARE_CENSUS rc={rc} kind={kind} stages={n} fallback={fallback} malformed={malformed} verified={int(verified)} boot_verified=0',verified

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('log size')
        row,verified=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V425_HARDWARE_AUDIT inspected=0');return 1
    print(row);print('V425_HARDWARE_AUDIT inspected=1');return 0 if verified else 1
if __name__=='__main__':raise SystemExit(main())
