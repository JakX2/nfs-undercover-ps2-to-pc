#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v922_irq_return as old
BEGIN=b'V928_LEAF_BEGIN original_resume=1 previous_ee=0'
BLR=b'V928_LEAF_BLR original_extract=1 previous_ee=0'
POLL=b'V928_LEAF_POLL original_blr=1 same_tick=1'
RETURN=b'V928_LEAF_RETURN original_leaf=1 original_blr=1 osinit_resume=1 previous_ee=0 integer_state=1 gqr=1 device_held=1 caller_instruction_executed=0 boot_verified=0'
FAULT=rb'V928_LEAF_INVALID kind=[1-5] reason=[0-5] stage=[0-5]'
def inspect(raw,rc):
    if len(raw)>old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if re.fullmatch(old.RESULT,l)]
    ok=False
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=old.old.old.old.old.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V928_',old.old.capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        ok=bool(valid and tail==[BEGIN,BLR,POLL,RETURN] and not any(l.startswith(b'V928_') for l in rows[:i+1]))
    return f'V928_LEAF_CENSUS rc={rc} verified={int(ok)} native_rfi={int(ok)} original_leaf_return={int(ok)} osinit_resume={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V928_LEAF_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (*old.old.capture.CAPTURE,*old.old.old.old.MARKERS,old.old.old.POLL,old.old.old.RETURN,old.old.RETURN,*old.STAGES,BEGIN,BLR,POLL,RETURN,old.old.old.old.old.STATUS,old.old.old.old.old.STORE) or any(re.fullmatch(p,l) for p in (old.RESULT,old.FAULT,FAULT,old.old.old.old.old.INDEX,old.old.old.old.old.JOIN,old.old.old.old.old.STOP,old.old.old.old.old.BAD)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
