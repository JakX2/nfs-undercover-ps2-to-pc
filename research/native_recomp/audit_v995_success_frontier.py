#!/usr/bin/env python3
"""Strictly classify the two verified successful-response continuations."""
import argparse,re
from pathlib import Path
import audit_v989_shared_time as shared
import audit_v986_transfer_frontier as transfer
import audit_v975_second_time as time
RESULT=rb'V995_CALLBACK_FRONTIER target_class=([0-4]) aligned=([01]) visits=([0-9]{1,4}) token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=(?:[1-9]|1[0-3]) stage=[0-4] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
TAGS=shared.old.old.old.handler.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V932_',b'V939_',b'V951_',b'V958_',b'V967_',b'V975_',b'V981_',b'V989_',b'V995_',shared.old.old.old.capture.PREFIX)
def inspect(raw,rc):
    if len(raw)>shared.old.old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(shared.old.RESULT,l)]
    ok=False;branch=admitted=category=visits=0
    if rc==0 and len(hits)==1:
        i=hits[0];_,base=shared.inspect(b'\n'.join(rows[:i+1]),0)
        tail=[l for l in rows[i+1:] if l.startswith(TAGS)]
        early=any(l.startswith((b'V975_',b'V981_',b'V995_')) for l in rows[:i+1])
        if base and not early:
            m=re.fullmatch(RESULT,tail[0]) if len(tail)==1 else None
            if m and 1<=int(m[1])<=4 and 1<=int(m[3])<=8192:
                ok=True;branch=6;category=int(m[1]);admitted=int(category==2 and m[2]==b'1');visits=int(m[3])
            elif len(tail)==2 and re.fullmatch(time.RESULT,tail[0]):
                m=re.fullmatch(transfer.RESULT,tail[1])
                if m and 1<=int(m[6])<=8192 and int(m[5])==int(all(int(x) for x in m.groups()[:4])):
                    t=re.fullmatch(time.RESULT,tail[0])
                    if 1<=int(t[1])<=8192:ok=True;branch=4;admitted=int(m[5]);visits=int(m[6])
    return f'V995_SUCCESS_CENSUS rc={rc} verified={int(ok)} branch={branch} admitted={admitted} target_class={category} visits={visits} call_executed=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>shared.old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V995_SUCCESS_AUDIT inspected=0');return 1
    # Reuse the existing sanitized predecessor output without publishing
    # any raw guest address, register value or original instruction word.
    for l in raw.splitlines():
        if l in (shared.old.old.BEGIN,shared.old.old.old.BEGIN,*shared.old.old.old.EDGES,shared.old.old.old.old.TRAMP,shared.old.old.old.old.old.SOURCE,shared.old.old.old.old.old.RFI,shared.old.old.old.old.old.POLL,*shared.old.old.old.old.old.STAGES) or any(re.fullmatch(p,l) for p in (RESULT,FAULT,transfer.RESULT,time.RESULT,shared.RESULT,shared.DIAG,shared.old.RESULT,shared.old.old.RESULT,shared.old.old.old.RESULT,shared.old.old.old.FAULT,shared.old.old.old.old.RESULT,shared.old.old.old.old.FAULT,shared.old.old.old.old.old.RESULT,shared.old.old.old.old.old.DIAG,shared.old.old.old.old.old.old.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
