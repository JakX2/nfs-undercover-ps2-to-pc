#!/usr/bin/env python3
"""Accept only the verified time prefix followed by restore/return or an exact next refusal."""
import argparse,re
from pathlib import Path
from audit_v742_handler_time import inspect as time,RESULT as TIME_RESULT,PREFIX as TIME,MAX_LOG
from audit_v738_handler_restore import inspect as restore,diagnostic as restore_diag,EVENTS as RESTORE_EVENTS,RESTORE
from audit_v747_time_suffix import inspect as suffix,diagnostic as suffix_diag
from audit_v726_handler_return import STAGES,RESULT
from audit_v709_os_leaves import MARKERS
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS+(b'V726_HANDLER_',TIME,RESTORE,b'V747_NEXT_'))]
    hits=[i for i,l in enumerate(rows) if re.fullmatch(TIME_RESULT,l)]
    time_ok=returned=boundary=False
    if len(hits)==1:
        i=hits[0];_,time_ok=time(b'\n'.join(rows[:i+1]),0)
        if time_ok:
            tail=rows[i+1:]
            if rc==0 and len(tail)==7 and tail[:3]==RESTORE_EVENTS and tail[3:6]==STAGES[1:] and re.fullmatch(RESULT,tail[6]):
                _,returned=restore(b'\n'.join(l for l in rows if not l.startswith(TIME)),0)
            elif rc==126 and not any(l.startswith(RESTORE) for l in rows):
                _,boundary=suffix(raw,rc)
    ok=bool(returned or boundary)
    return f'V760_COMBINED_CENSUS rc={rc} time_return={int(time_ok)} restore_return={int(returned)} handler_return={int(returned)} verified_boundary={int(boundary)} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V760_COMBINED_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if suffix_diag(l) or restore_diag(l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
