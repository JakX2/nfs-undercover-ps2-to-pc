#!/usr/bin/env python3
"""Allowlist only bounded, privacy-safe complete-image startup evidence."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
MAX_LOG=8*1024*1024
STAGES=[f'V419_FULL_START_STAGE n={i} valid=1'.encode() for i in (1,2,3)]
RESULT=b'V419_FULL_START_RESULT entry=1 registers=1 hardware_entry=1 fallback=0 boot_verified=0'
MARKERS=(b'V419_FULL_START_STAGE',b'V419_FULL_START_RESULT',b'V419_FULL_START_INVALID',b'V419_FULL_START_FALLBACK')

def inspect(raw:bytes,rc:int)->tuple[str,bool]:
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('log geometry')
    lines=[line for line in raw.splitlines() if line.startswith(MARKERS)]
    # Accept partial ordered stages as evidence, never as a successful gate.
    n=0
    for stage in STAGES:
        if n>=len(lines) or lines[n]!=stage:break
        n+=1
    fallback=int(any(line==b'V419_FULL_START_FALLBACK hit=1' for line in lines))
    malformed=int(any(line not in STAGES+[RESULT,b'V419_FULL_START_FALLBACK hit=1'] and not re.fullmatch(rb'V419_FULL_START_INVALID stage=[0-3]',line) for line in lines))
    verified=rc==0 and lines==STAGES+[RESULT]
    kind='zero' if rc==0 else 'timeout' if rc in (124,137) else 'signal' if rc>=128 else 'nonzero'
    return (f'V419_FULL_START_CENSUS rc={rc} kind={kind} stages={n} fallback={fallback} malformed={malformed} verified={int(verified)} boot_verified=0',verified)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('log size')
        row,verified=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V419_FULL_START_AUDIT inspected=0');return 1
    print(row);print('V419_FULL_START_AUDIT inspected=1');return 0 if verified else 1
if __name__=='__main__':raise SystemExit(main())
