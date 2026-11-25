#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v709_os_leaves import inspect as prior,MARKERS,MAX_LOG
from audit_v699_si_postack import END
from audit_v726_handler_return import diagnostic as old
PREFIX=b'V742_TIME_'
STAGES=[b'V726_HANDLER_STAGE n=2',b'V742_TIME_STAGE n=1',b'V742_TIME_STAGE n=2',
        *[f'V742_TIME_LEAF ordinal={i} n={j}'.encode() for i in range(1,4) for j in range(1,4)],b'V742_TIME_STAGE n=3']
RESULT=rb'V742_TIME_RESULT returned=1 abi=1 leaves=3 visits=25 total=([1-9][0-9]{1,2}) handler_return=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS+(b'V726_HANDLER_',PREFIX))]
    i=rows.index(END) if rows.count(END)==1 else -1
    ok_prior=False
    if i>=0:_,ok_prior=prior(b'\n'.join(rows[:i+1]),0)
    tail=rows[i+1:] if i>=0 else rows
    match=re.fullmatch(RESULT,tail[-1]) if tail else None
    ok=bool(rc==0 and ok_prior and match and tail[:-1]==STAGES and 45<=int(match[1])<=128 and not any(l.startswith((PREFIX,b'V726_HANDLER_')) for l in rows[:i+1]))
    return f'V742_TIME_CENSUS rc={rc} second_return={int(ok_prior)} stages={sum(l in tail for l in STAGES)} verified={int(ok)} boot_verified=0',ok
def diagnostic(l):
    return old(l) or re.fullmatch(rb'V742_TIME_STAGE n=[1-3]|V742_TIME_LEAF ordinal=[1-3] n=[1-3]|V742_TIME_INVALID reason=[1-8] stage=[0-4] leaf=[1-4] witness=[0-6] trace=[0-9]{1,2}|V726_HANDLER_INVALID kind=[1-5] witness=8 stage=[0-5] visits=[0-9]{1,4} polls=[0-9]{1,4}|'+RESULT,l) is not None
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V742_TIME_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if diagnostic(l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
