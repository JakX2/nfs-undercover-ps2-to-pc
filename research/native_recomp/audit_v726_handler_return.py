#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v709_os_leaves import inspect as prior,MARKERS,MAX_LOG,public_diagnostic
from audit_v699_si_postack import END
PREFIX=b'V726_HANDLER_'
STAGES=[f'V726_HANDLER_STAGE n={i}'.encode() for i in range(2,6)]
RESULT=rb'V726_HANDLER_RESULT returned=1 abi=1 dispatch_resume=1 visits=([1-9][0-9]{0,3}) polls=([0-9]{1,4}) rfi_return=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS+(PREFIX,))]
    i=rows.index(END) if rows.count(END)==1 else -1
    ok_prior=False
    if i>=0:_,ok_prior=prior(b'\n'.join(rows[:i+1]),0)
    tail=rows[i+1:] if i>=0 else rows
    match=re.fullmatch(RESULT,tail[-1]) if tail else None
    ok=bool(rc==0 and ok_prior and match and tail[:-1]==STAGES and 1<=int(match[1])<=1024 and int(match[2])<=int(match[1]) and not any(l.startswith(PREFIX) for l in rows[:i+1]))
    return f'V726_HANDLER_CENSUS rc={rc} second_return={int(ok_prior)} handler_stages={sum(l in tail for l in STAGES)} verified={int(ok)} rfi_return=0 boot_verified=0',ok
def diagnostic(l):
    return public_diagnostic(l) or re.fullmatch(rb'V726_HANDLER_STAGE n=[2-5]|V726_HANDLER_INVALID kind=[1-5] witness=[0-7] stage=[0-5] visits=[0-9]{1,4} polls=[0-9]{1,4}|V726_HANDLER_CONTROL ordinal=[0-9]{1,3} kind=[0-2] opcode=[0-9]{1,2}|'+RESULT,l) is not None
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V726_HANDLER_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if diagnostic(l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
