#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v922_irq_return as old
SOURCE=b'V932_PENDING_SOURCE held_completion=1 only_si=1'
RFI=b'V932_RFI_REENTRY restored_integer=1 native_rfi=1 second_exception=1 same_tick=1'
POLL=b'V932_REENTRY_POLL same_tick=1 no_guest_instruction=1'
RESULT=rb'V932_REENTRY_RESULT native_rfi=1 second_exception=1 vector_entry=1 restored_context=1 visits=([0-9]{1,3}) device_held=1 resumed_instruction_executed=0 boot_verified=0'
DIAG=rb'V932_IRQ_BEGIN_REFUSAL mask=[0-9]{1,3}'
def inspect(raw,rc):
    if len(raw)>old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l==old.old.RETURN];ok=False;visits=0
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=old.old.old.old.old.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V932_',old.old.capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        m=re.fullmatch(RESULT,tail[-1]) if tail else None
        ok=bool(valid and m and 1<=int(m[1])<=512 and tail[:-1]==[SOURCE,*old.STAGES[:2],RFI,POLL] and
            not any(l.startswith((b'V922_',b'V932_')) for l in rows[:i+1]))
        if ok:visits=int(m[1])
    return f'V932_REENTRY_CENSUS rc={rc} verified={int(ok)} native_rfi={int(ok)} second_vector={int(ok)} visits={visits} original_resume_executed=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V932_REENTRY_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (old.old.RETURN,SOURCE,RFI,POLL,*old.STAGES) or any(re.fullmatch(p,l) for p in (RESULT,DIAG,old.FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
