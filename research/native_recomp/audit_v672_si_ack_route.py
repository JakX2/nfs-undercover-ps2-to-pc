#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v667_si_dispatch import MARKERS as PRIOR,MAX_LOG,inspect as inspect_dispatch
PREFIX=b'V672_SI_ACK_'
EVENTS=[b'V672_SI_ACK_STAGE n=1',b'V672_SI_ACK_STAGE n=2']
RESULT=b'V672_SI_ACK_RESULT guest_store=1 tc_w1c=1 pi_deasserted=1 mask_preserved=1 next_label=1 rfi_return=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(PRIOR+(PREFIX,))]
    i=next((i for i,l in enumerate(rows) if l.startswith(PREFIX)),len(rows))
    _,prior=inspect_dispatch(b'\n'.join(rows[:i]),0)
    tail=rows[i:];n=0
    for a,b in zip(tail,EVENTS):
        if a!=b:break
        n+=1
    ok=bool(rc==0 and prior and tail==EVENTS+[RESULT])
    return f'V672_SI_ACK_CENSUS rc={rc} dispatch={int(prior)} stages={n} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V672_SI_ACK_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V672_SI_ACK_INVALID reason=[1-6] trace=[0-7]|V673_SI_ACK_CALL ordinal=[0-9]{1,2} kind=[0-2]|V667_SI_DISPATCH_INVALID reason=[1-6] stage=[0-6]|V663_EXTERNAL_INVALID reason=[1-9] stage=[0-6]|V663_EXTERNAL_PENDING active=[0-9]{1,10}|V670_VECTOR_REFUSAL mask=[0-9]{1,4}',l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
