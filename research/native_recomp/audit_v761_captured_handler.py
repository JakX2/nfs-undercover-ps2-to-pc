#!/usr/bin/env python3
"""Verify the actual saved interrupted context and later handler in one run."""
import argparse,re
from pathlib import Path
from audit_v751_cold_capture import inspect as capture,PREFIX as CAP,CAPTURE,RESULT as ENTRY_RESULT,MAX_LOG
from audit_v760_combined_handler import inspect as combined
from audit_v747_time_suffix import diagnostic as suffix_diag
from audit_v738_handler_restore import diagnostic as restore_diag
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l==ENTRY_RESULT]
    saved=False
    if len(hits)==1:
        i=hits[0]
        _,saved=capture(b'\n'.join(rows[:i+1]),0)
        saved=bool(saved and not any(l.startswith(CAP) for l in rows[i+1:]))
    result,ok=combined(raw,rc)
    ok=bool(ok and saved)
    return result,f'V761_CAPTURED_CENSUS rc={rc} saved_context={int(saved)} combined_route={int(ok)} rfi_return=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();prior,row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V761_CAPTURED_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in CAPTURE or suffix_diag(l) or restore_diag(l) or re.fullmatch(rb'V751_CAPTURE_INVALID valid=[01] gprs=[0-9]{1,2} special=[0-9]{1,2}|V663_EXTERNAL_INVALID reason=1[01] stage=[0-6]',l):print(l.decode())
    print(prior);print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
