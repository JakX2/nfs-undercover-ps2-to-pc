#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v921_capture_join as old
STAGES=[f'V922_IRQ_RETURN_STAGE n={i}'.encode() for i in range(1,6)]
RESULT=rb'V922_IRQ_RETURN_RESULT original_context=1 scheduler=1 native_rfi=1 original_resume=1 visits=([0-9]{1,3}) device_held=1 resumed_instruction_executed=0 boot_verified=0'
FAULT=rb'V922_IRQ_RETURN_INVALID kind=[1-5] reason=[0-9] stage=[0-5] visits=[0-9]{1,3}'
def inspect(raw,rc):
    if len(raw)>old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l==old.RETURN];ok=False;visits=0
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=old.old.old.old.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',old.capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        m=re.fullmatch(RESULT,tail[-1]) if tail else None
        ok=bool(valid and m and 1<=int(m[1])<=512 and tail[:-1]==STAGES and not any(l.startswith(b'V922_') for l in rows[:i+1]))
        if ok:visits=int(m[1])
    return f'V922_IRQ_RETURN_CENSUS rc={rc} verified={int(ok)} native_rfi={int(ok)} original_resume={int(ok)} visits={visits} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V922_IRQ_RETURN_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (*old.capture.CAPTURE,*old.old.old.MARKERS,old.old.POLL,old.old.RETURN,old.RETURN,*STAGES,old.old.old.old.STATUS,old.old.old.old.STORE) or any(re.fullmatch(p,l) for p in (RESULT,FAULT,old.old.old.old.INDEX,old.old.old.old.JOIN,old.old.old.old.STOP,old.old.old.old.BAD)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
