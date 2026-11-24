#!/usr/bin/env python3
"""Privacy-safe continuation gate; reject fallback, malformed and duplicate markers."""
import argparse
from pathlib import Path
import re
from audit_v430_full_data import MAX_LOG,inspect as inspect_data
BEGIN=re.compile(rb'V433_OS_BEGIN arena_hi_nonzero=([01]) boot_info_nonzero=([01])')
DB=b'V433_OS_DB_ENTRY valid=1'
RESULT=b'V433_OS_RESULT db_return=1 debug_stores=4 os_entry=1 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V433_OS_INVALID reason=([1-6]) stage=([0-3])')
PREFIX=(b'V425_HARDWARE_',b'V428_CACHE_',b'V430_DATA_',b'V433_OS_')
def inspect(raw:bytes,rc:int):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX)]
    i=next((i for i,l in enumerate(lines) if l.startswith(b'V433_OS_')),len(lines))
    data_row,data_ok=inspect_data(b'\n'.join(lines[:i]),0)
    tail=lines[i:]
    begin=BEGIN.fullmatch(tail[0]) if tail else None
    db=bool(begin and len(tail)>=2 and tail[1]==DB)
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    invalid=[m for l in tail if (m:=INVALID.fullmatch(l))]
    reason=int(invalid[0][1]) if len(invalid)==1 else 0
    verified=bool(rc==0 and data_ok and begin and db and tail[2:]==[RESULT] and not fallback)
    arena=int(begin[1]) if begin else 0
    info=int(begin[2]) if begin else 0
    return (f'V433_OS_CENSUS rc={rc} data={int(data_ok)} begin={int(bool(begin))} db={int(db)} os_entry={int(verified)} arena_hi_nonzero={arena} boot_info_nonzero={info} fallback={fallback} reason={reason} verified={int(verified)} boot_verified=0',verified)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V433_OS_AUDIT inspected=0');return 1
    print(row);print('V433_OS_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
