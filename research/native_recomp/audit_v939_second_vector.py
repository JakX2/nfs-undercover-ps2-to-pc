#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v932_pending_rfi as old
TRAMP=b'V939_SECOND_TRAMPOLINE original_vector=1 partial_context=1'
RESULT=rb'V939_SECOND_RESULT original_vector=1 original_trampoline=1 saved_fields=38 vector_visits=([0-9]{1,3}) trampoline_visits=([0-9]{1,3}) second_dispatcher_entry=1 device_held=1 dispatcher_instruction_executed=0 boot_verified=0'
FAULT=rb'V939_SECOND_INVALID kind=[1-4] reason=[0-6] stage=[0-3] vector=[0-9]{1,3} trampoline=[0-9]{1,3} gpr_mask=[0-9]{1,10} special_mask=[0-9]{1,2}'
def inspect(raw,rc):
    if len(raw)>old.old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(old.RESULT,l)]
    ok=False;v=t=0
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=old.old.old.old.old.old.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V932_',b'V939_',old.old.old.capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        m=re.fullmatch(RESULT,tail[-1]) if tail else None
        ok=bool(valid and m and tail[:-1]==[TRAMP] and 1<=int(m[1])<=128 and 1<=int(m[2])<=128 and not any(l.startswith(b'V939_') for l in rows[:i+1]))
        if ok:v,t=int(m[1]),int(m[2])
    return f'V939_SECOND_CENSUS rc={rc} verified={int(ok)} vector_visits={v} trampoline_visits={t} saved_fields={38*int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V939_SECOND_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (old.SOURCE,old.RFI,old.POLL,TRAMP,*old.old.STAGES) or any(re.fullmatch(p,l) for p in (old.RESULT,old.DIAG,old.old.FAULT,RESULT,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
