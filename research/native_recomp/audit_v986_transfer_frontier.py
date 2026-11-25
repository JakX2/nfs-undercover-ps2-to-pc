#!/usr/bin/env python3
"""Verify the complete original time route and read-only transfer frontier."""
import argparse,re
from pathlib import Path
import audit_v975_second_time as old
RESULT=rb'V981_TRANSFER_FRONTIER type=([01]) idle=([01]) queue_match=([01]) callback_known=([01]) admitted=([01]) visits=([0-9]{1,4}) token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=(?:[1-9]|10|11) stage=[0-4] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
def inspect(raw,rc):
    if len(raw)>old.old.old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(old.RESULT,l)]
    ok=False;admitted=visits=0
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=old.old.old.old.handler.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V932_',b'V939_',b'V951_',b'V958_',b'V967_',b'V975_',b'V981_',old.old.old.old.capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        m=re.fullmatch(RESULT,tail[0]) if len(tail)==1 else None
        if valid and m and 1<=int(m[6])<=8192 and not any(l.startswith(b'V981_') for l in rows[:i+1]):
            values=tuple(int(x) for x in m.groups()[:5])
            if values[4]==int(all(values[:4])):
                ok=True;admitted=values[4];visits=int(m[6])
    return f'V986_FRONTIER_CENSUS rc={rc} verified={int(ok)} admitted={admitted} visits={visits} call_executed=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V986_FRONTIER_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (old.old.old.BEGIN,old.old.old.old.BEGIN,*old.old.old.old.EDGES,old.old.old.old.old.TRAMP,old.old.old.old.old.old.SOURCE,old.old.old.old.old.old.RFI,old.old.old.old.old.old.POLL,*old.old.old.old.old.old.old.STAGES) or any(re.fullmatch(p,l) for p in (RESULT,FAULT,old.RESULT,old.old.RESULT,old.old.old.RESULT,old.old.old.old.RESULT,old.old.old.old.FAULT,old.old.old.old.old.RESULT,old.old.old.old.old.FAULT,old.old.old.old.old.old.RESULT,old.old.old.old.old.old.DIAG,old.old.old.old.old.old.old.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
