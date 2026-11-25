#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v939_second_vector as old
import audit_v870_handler_suffix as handler
import audit_v751_cold_capture as capture
BEGIN=b'V951_DISPATCH_BEGIN captured_context=1 held_token=1'
EDGES=[f'V951_DISPATCH_EDGE n={n}'.encode() for n in range(1,6)]
RESULT=rb'V951_DISPATCH_RESULT original_dispatcher=1 original_leaves=4 pi_reads=1 handler_entry=1 saved_fields=38 visits=([0-9]{1,4}) device_held=1 handler_instruction_executed=0 boot_verified=0'
FAULT=rb'V951_DISPATCH_INVALID kind=[1-4] stage=[0-6] reason=[0-5] visits=[0-9]{1,4}'
def inspect(raw,rc):
    if len(raw)>capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(old.RESULT,l)]
    ok=False;visits=0
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=handler.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V932_',b'V939_',b'V951_',capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        m=re.fullmatch(RESULT,tail[-1]) if tail else None
        ok=bool(valid and m and tail[:-1]==[BEGIN,*EDGES] and 1<=int(m[1])<=2048 and not any(l.startswith(b'V951_') for l in rows[:i+1]))
        if ok:visits=int(m[1])
    return f'V951_DISPATCH_CENSUS rc={rc} verified={int(ok)} original_dispatcher={int(ok)} handler_entry={int(ok)} visits={visits} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V951_DISPATCH_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (BEGIN,*EDGES,old.TRAMP,old.old.SOURCE,old.old.RFI,old.old.POLL,*old.old.old.STAGES) or any(re.fullmatch(p,l) for p in (RESULT,FAULT,old.RESULT,old.FAULT,old.old.RESULT,old.old.DIAG,old.old.old.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
