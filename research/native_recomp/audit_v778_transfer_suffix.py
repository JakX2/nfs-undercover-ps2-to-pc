#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v777_transfer_return import inspect as transfer,RESULT as TRANSFER,ENTRY,HANDOFF,PREFIX
from audit_v742_handler_time import diagnostic as prior,MAX_LOG
from audit_v747_time_suffix import CONTROL,INVALID
BOUNDARY=rb'V778_NEXT_BOUNDARY ordinal=([5-9]|1[0-2]) kind=([12]) visits=([1-9][0-9]{0,3}) polls=([0-9]{1,4}) follow=([023]) executed=0'
BLR=rb'V778_HANDLER_BLR abi=1 visits=([1-9][0-9]{0,3}) polls=([0-9]{1,4}) follow=([023]) executed=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(TRANSFER,l)]
    ok=False;ordinal=kind=follow=0;blr=False
    if len(hits)==1:
        i=hits[0];_,valid=transfer(b'\n'.join(rows[:i+1]),0)
        tail=[l for l in rows[i+1:] if l.startswith(PREFIX+(b'V778_',b'V726_HANDLER_',b'V747_NEXT_'))]
        m=re.fullmatch(TRANSFER,rows[i]);old=int(m[5])
        def held(f):return (old==f==0) or (old==2 and f in (2,3)) or (old==f==3)
        if valid and rc==126 and len(tail)==3:
            a,b,c=(re.fullmatch(p,l) for p,l in zip((CONTROL,BOUNDARY,INVALID),tail))
            if a and b and c:
                ordinal,kind,v,p,follow=map(int,b.groups())
                ok=bool(a.groups()[:2]==b.groups()[:2] and b.groups()[2:4]==c.groups() and
                        v<=1024 and p<=v and held(follow) and (a[2],a[3]) in ((b'1',b'18'),(b'2',b'19')))
        elif valid and rc==0 and len(tail)==1:
            b=re.fullmatch(BLR,tail[0])
            if b:
                v,p,follow=map(int,b.groups());ok=bool(v<=1024 and p<=v and held(follow));blr=ok
    return f'V778_SUFFIX_CENSUS rc={rc} next_ordinal={ordinal if ok else 0} next_kind={kind if ok else 0} follow={follow if ok else 0} blr_boundary={int(blr)} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V778_SUFFIX_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if prior(l) or l==HANDOFF or any(re.fullmatch(p,l) for p in (ENTRY,TRANSFER,BOUNDARY,BLR)):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
