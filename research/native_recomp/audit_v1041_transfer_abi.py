#!/usr/bin/env python3
"""Independently validate a proposed six-argument admission, not execution."""
import argparse,re
from pathlib import Path
import audit_v1021_error_frontier as old
from audit_second_irq_output_v1016 import public_line
ABI=rb'V1040_TRANSFER_ABI admission=([0-2]) timing_only=([01]) unchanged_slot=([01]) call_executed=0 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=18 stage=[0-5] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
TAGS=old.TAGS+(b'V1040_',b'V1041_')
def inspect(raw,rc):
    if len(raw)>old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if l.startswith((b'V1040_',b'V1041_'))]
    ok=False;admission=0
    if rc==0 and len(hits)==1:
        i=hits[0];mark=re.fullmatch(ABI,rows[i])
        prior=b'\n'.join(rows[:i]);line,base=old.inspect(prior,rc)
        if mark and base and 'branch=4' in line and not any(l.startswith(TAGS) for l in rows[i+1:]):
            tail=[l for l in rows[:i] if l.startswith(old.TAGS)]
            if len(tail)>=3:
                d=re.fullmatch(old.DETAIL,tail[-3]);h=re.fullmatch(old.HISTORY,tail[-2]);t=re.fullmatch(old.transfer.RESULT,tail[-1])
                if d and h and t:
                    mask,slot,_,_=map(int,d.groups());initial,current,changed,initial_slot,samples=map(int,h.groups())
                    typ,idle,match,callback,legacy,_=map(int,t.groups())
                    valid=0<=mask<=255 and 0<=initial<=255 and 0<=current<=255 and 0<=changed<=255 and 1<=samples<=8192 and current==mask and not ((initial^current)&~changed) and match==int(mask==0) and legacy==int(typ and idle and match and callback)
                    if valid:
                        unchanged=int(changed==0 and initial_slot==1)
                        expected=1 if legacy else 2 if (typ and idle and callback and slot==1 and mask in (64,128,192) and unchanged and initial==current) else 0
                        got,tail_only,still=map(int,mark.groups())
                        ok=got==expected and tail_only==int(expected==2) and still==unchanged
                        admission=expected if ok else 0
    return f'V1041_ABI_CENSUS verified={int(ok)} admission={admission} original_transfer_executed=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1041_ABI_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_line(l,(old.ack.BEGIN,old.error.RESULT,old.DIRECT,old.INDIRECT),(old.FAULT,old.frontier.RESULT,old.frontier.FAULT,old.time.RESULT,old.transfer.RESULT,old.shared.DETAIL,old.shared.DIAG,old.shared.RESULT,old.post.RESULT,old.ack.RESULT,old.DETAIL,old.HISTORY,ABI,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
