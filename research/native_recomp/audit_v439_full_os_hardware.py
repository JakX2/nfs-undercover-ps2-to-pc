#!/usr/bin/env python3
"""Exact privacy-safe full-image OSInit hardware continuation gate."""
import argparse
from pathlib import Path
import re
from audit_v435_full_os_time import PREFIX,MARK,inspect as inspect_time,MAX_LOG
HW=b'V439_HW_'
BEGIN=re.compile(rb'V439_HW_BEGIN copy=([01])')
COPY=b'V439_HW_COPY valid=1'
STAGES=[f'V439_HW_STAGE n={i} valid=1'.encode() for i in range(1,14)]
HEX_STAGES=[f'V439_HW_STAGE n={i:x} valid=1'.encode() for i in range(1,14)]
RESULT=b'V439_HW_RESULT exec=1 perf=6 hid4=1 hid0=1 fpscr=1 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V439_HW_INVALID reason=([1-8]) stage=([0-9]|1[0-3])')
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX+(MARK,HW))]
    i=next((i for i,l in enumerate(lines) if l.startswith(HW)),len(lines))
    _,time_ok=inspect_time(b'\n'.join(lines[:i]),0)
    tail=lines[i:]
    begin=BEGIN.fullmatch(tail[0]) if tail else None
    copy=int(begin[1]) if begin else 0
    expected=STAGES[:1]+([COPY] if copy else [])+STAGES[1:]+[RESULT]
    matched=0;stages=0
    if begin:
        for a,b in zip(tail[1:],expected):
            if a!=b:break
            matched+=1
            if a in STAGES:stages+=1
    invalid=[m for l in tail if (m:=INVALID.fullmatch(l))]
    reason=int(invalid[0][1]) if len(invalid)==1 else 0
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and time_ok and begin and tail[1:]==expected and not fallback)
    # Diagnostic only: the exact legacy hex sequence does not pass the canonical gate.
    legacy=HEX_STAGES[:1]+([COPY] if copy else [])+HEX_STAGES[1:]+[RESULT]
    legacy_hex=int(bool(rc==0 and time_ok and begin and tail[1:]==legacy and not fallback))
    terminal=int(tail.count(RESULT)==1)
    return f'V439_HW_CENSUS rc={rc} time={int(time_ok)} stages={stages} matched={matched} copy={copy} fallback={fallback} reason={reason} terminal={terminal} legacy_hex_complete={legacy_hex} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V439_HW_AUDIT inspected=0');return 1
    print(row);print('V439_HW_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
