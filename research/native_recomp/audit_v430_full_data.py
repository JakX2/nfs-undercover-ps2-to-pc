#!/usr/bin/env python3
"""Privacy-safe full-image data-initialization gate."""
import argparse
from pathlib import Path
import re
from audit_v428_full_cache import STAGES as CACHE,MAX_LOG
BEGIN=re.compile(rb'V430_DATA_BEGIN before_nonzero=([0-9]{1,6})')
HELPERS=[f'V430_DATA_HELPER n={i} valid=1'.encode() for i in range(1,7)]
RESULT=b'V430_DATA_RESULT helpers=6 bss_bytes=963456 return=1 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V430_DATA_INVALID reason=([1-9]) calls=([0-6])')
def inspect(raw:bytes,rc:int):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith((b'V425_HARDWARE_',b'V428_CACHE_',b'V430_DATA_'))]
    prefix=0
    for stage in CACHE:
        if prefix>=len(lines) or lines[prefix]!=stage:break
        prefix+=1
    start=BEGIN.fullmatch(lines[prefix]) if prefix==len(CACHE) and prefix<len(lines) else None
    before=int(start[1]) if start else 0
    began=bool(start and before<=963456)
    offset=prefix+int(began);count=0
    if began:
        for marker in HELPERS:
            if offset+count>=len(lines) or lines[offset+count]!=marker:break
            count+=1
    failures=[m for l in lines if (m:=INVALID.fullmatch(l))]
    reason=int(failures[0][1]) if len(failures)==1 else 0
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    verified=rc==0 and began and prefix==len(CACHE) and count==6 and lines[offset+count:]==[RESULT]
    return f'V430_DATA_CENSUS rc={rc} hardware={min(prefix,9)} cache={max(prefix-9,0)} begin={int(began)} helpers={count} before_nonzero={before if began else 0} fallback={fallback} reason={reason} verified={int(verified)} boot_verified=0',verified

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V430_DATA_AUDIT inspected=0');return 1
    print(row);print('V430_DATA_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
