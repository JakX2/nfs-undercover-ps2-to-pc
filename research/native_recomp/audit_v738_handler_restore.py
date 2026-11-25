#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v726_handler_return import inspect as prior,diagnostic as old,MAX_LOG,STAGES,PREFIX
from audit_v709_os_leaves import MARKERS
RESTORE=b'V738_RESTORE_'
EVENTS=[f'V738_RESTORE_STAGE n={i}'.encode() for i in range(1,4)]
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS+(PREFIX,RESTORE))]
    _,ok_prior=prior(b'\n'.join(l for l in rows if not l.startswith(RESTORE)),rc)
    restore=[l for l in rows if l.startswith(RESTORE)]
    ok=bool(ok_prior and restore==EVENTS and rows.index(STAGES[0])<rows.index(EVENTS[0]) and
            rows[rows.index(EVENTS[0]):rows.index(EVENTS[0])+3]==EVENTS and rows.index(EVENTS[-1])<rows.index(STAGES[1]))
    return f'V738_RESTORE_CENSUS rc={rc} handler_return={int(ok_prior)} restore_stages={sum(l in restore for l in EVENTS)} verified={int(ok)} boot_verified=0',ok
def diagnostic(l):
    return old(l) or re.fullmatch(rb'V738_RESTORE_STAGE n=[1-3]|V738_RESTORE_INVALID kind=[1-4] witness=[0-6] stage=[0-4]|V726_HANDLER_INVALID kind=[1-5] witness=8 stage=[0-5] visits=[0-9]{1,4} polls=[0-9]{1,4}',l) is not None
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V738_RESTORE_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if diagnostic(l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
