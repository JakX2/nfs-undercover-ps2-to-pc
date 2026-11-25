#!/usr/bin/env python3
"""Prove the earlier return and a subsequent refused linked call, not boot."""
import argparse,re
from pathlib import Path
from audit_v742_handler_time import inspect as time,diagnostic as prior,RESULT,MAX_LOG,PREFIX
from audit_v726_handler_return import inspect as handler
BOUNDARY=rb'V747_NEXT_BOUNDARY ordinal=([4-9]|1[0-2]) kind=([12]) visits=([1-9][0-9]{0,3}) polls=([0-9]{1,4}) executed=0'
CONTROL=rb'V726_HANDLER_CONTROL ordinal=([4-9]|1[0-2]) kind=([12]) opcode=(18|19)'
INVALID=rb'V726_HANDLER_INVALID kind=3 witness=4 stage=2 visits=([1-9][0-9]{0,3}) polls=([0-9]{1,4})'
from audit_v709_os_leaves import MARKERS
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS+(b'V726_HANDLER_',PREFIX,b'V747_NEXT_'))]
    hits=[i for i,l in enumerate(rows) if re.fullmatch(RESULT,l)]
    i=hits[0] if len(hits)==1 else -1
    ok_time=False;ok=False;ordinal=0;kind=0
    if i>=0:
        _,ok_time=time(b'\n'.join(rows[:i+1]),0)
        tail=rows[i+1:]
        if ok_time and rc==126 and len(tail)==3:
            a,b,c=(re.fullmatch(p,l) for p,l in zip((CONTROL,BOUNDARY,INVALID),tail))
            if a and b and c and a.groups()[:2]==b.groups()[:2] and b.groups()[2:]==c.groups() and int(b[3])<=1024 and int(b[4])<=int(b[3]) and (a[2],a[3]) in ((b'1',b'18'),(b'2',b'19')):
                ok=True;ordinal=int(b[1]);kind=int(b[2])
        if ok_time and rc==0:
            _,ok=handler(b'\n'.join(l for l in rows if not l.startswith(PREFIX)),0)
    return f'V747_SUFFIX_CENSUS rc={rc} time_return={int(ok_time)} next_ordinal={ordinal} next_kind={kind} verified_boundary={int(ok)} handler_return={int(ok and rc==0)} boot_verified=0',ok
def diagnostic(l):return prior(l) or re.fullmatch(BOUNDARY,l) is not None
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V747_SUFFIX_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if diagnostic(l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
