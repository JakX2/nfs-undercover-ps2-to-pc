#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v761_captured_handler import inspect as captured,MAX_LOG,CAPTURE
from audit_v726_handler_return import RESULT as HANDLER
from audit_v747_time_suffix import diagnostic as suffix_diag
from audit_v738_handler_restore import diagnostic as restore_diag
PREFIX=b'V767_EPILOGUE_'
STAGES=[f'V767_EPILOGUE_STAGE n={i}'.encode() for i in range(1,6)]
RESULT=rb'V767_EPILOGUE_RESULT live_context=1 scheduler=1 native_rfi=1 original_resume=1 visits=([0-9]{1,3}) resumed_instruction_executed=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if re.fullmatch(HANDLER,l)]
    events=[l for l in rows if l.startswith(PREFIX)]
    verified=boundary=False
    if len(hits)==1:
        i=hits[0];_,_,prior=captured(b'\n'.join(rows[:i+1]),0)
        m=re.fullmatch(RESULT,events[-1]) if events else None
        verified=bool(rc==0 and prior and m and 1<=int(m[1])<=512 and events[:-1]==STAGES and not any(l.startswith(PREFIX) for l in rows[:i+1]))
    elif not events and rc==126:
        _,_,boundary=captured(raw,rc)
    return f'V767_EPILOGUE_CENSUS rc={rc} verified_boundary={int(boundary)} native_rfi={int(verified)} original_resume={int(verified)} verified={int(verified or boundary)} boot_verified=0',bool(verified or boundary)
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V767_EPILOGUE_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in CAPTURE or suffix_diag(l) or restore_diag(l) or l in STAGES or re.fullmatch(RESULT,l) or re.fullmatch(rb'V767_EPILOGUE_INVALID kind=[1-6] reason=[0-9] stage=[0-5] visits=[0-9]{1,3}',l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
