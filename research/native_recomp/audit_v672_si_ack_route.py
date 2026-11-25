#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v667_si_dispatch import MARKERS as PRIOR,MAX_LOG,inspect as inspect_dispatch
PREFIX=b'V672_SI_ACK_'
FAILURES=(b'V673_SI_ACK_CALL ',b'V677_SI_ACK_WRITE_INVALID ',b'V680_SI_HELPER_INVALID ',b'V688_SI_SECOND_INVALID ',b'V688_SI_SECOND_CALL ',b'V693_SI_NESTED_INVALID ',b'V693_SI_NESTED_CALL ',b'V697_SI_READ_INVALID ',b'V697_SI_ACCESS_INVALID ',b'V699_POSTACK_',b'V709_OS_LEAF_',b'V711_POST_CONTROL ')
HELPER=b'V680_SI_HELPER_STAGE '
SECOND=b'V688_SI_SECOND_STAGE '
SECOND_ACK=b'V688_SI_SECOND_ACK '
NESTED=b'V693_SI_NESTED_STAGE '
NESTED_ACK=b'V693_SI_NESTED_ACK '
MARKERS=PRIOR+(PREFIX,HELPER,SECOND,SECOND_ACK,NESTED,NESTED_ACK)+FAILURES
EVENTS=[b'V672_SI_ACK_STAGE n=1',b'V672_SI_ACK_STAGE n=2']
RESULT=b'V672_SI_ACK_RESULT guest_store=1 tc_w1c=1 pi_deasserted=1 mask_preserved=1 next_label=1 rfi_return=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(rows) if l.startswith((PREFIX,)+FAILURES)),len(rows))
    _,prior=inspect_dispatch(b'\n'.join(rows[:i]),0)
    tail=rows[i:];n=0
    for a,b in zip((r for r in tail if r.startswith(PREFIX)),EVENTS):
        if a!=b:break
        n+=1
    helper_events=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
    extended=EVENTS[:1]+helper_events+EVENTS[1:]+[RESULT]
    second_events=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,4)]
    second_return=EVENTS[:1]+helper_events+second_events+EVENTS[1:]+[RESULT]
    second_ack=EVENTS[:1]+helper_events+second_events[:2]+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT]
    nested_events=[f'V693_SI_NESTED_STAGE n={i}'.encode() for i in range(1,4)]
    base=EVENTS[:1]+helper_events+second_events[:2]
    nested_ack=base+nested_events[:2]+[b'V693_SI_NESTED_ACK n=1']+EVENTS[1:]+[RESULT]
    nested_to_second=base+nested_events+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT]
    nested_to_handler=base+nested_events+second_events[2:]+EVENTS[1:]+[RESULT]
    ok=bool(rc==0 and prior and tail in (EVENTS+[RESULT],extended,second_return,second_ack,nested_ack,nested_to_second,nested_to_handler))
    helper_count=sum(r in tail for r in helper_events)
    second_count=sum(r in tail for r in second_events)
    return f'V672_SI_ACK_CENSUS rc={rc} dispatch={int(prior)} stages={n} helper_stages={helper_count} second_stages={second_count} nested_stages={sum(r in tail for r in nested_events)} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V672_SI_ACK_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V672_SI_ACK_INVALID reason=[1-6] trace=[0-8]|V673_SI_ACK_CALL ordinal=[0-9]{1,2} kind=[0-2]|V677_SI_ACK_WRITE_INVALID trace=[1-7]|V711_POST_CONTROL kind=[1-3] channel=[0-3] geometry=[01] type=[01] mask=[01] reserved=[01]|V680_SI_HELPER_INVALID reason=[0-5] stage=[0-4]|V680_SI_HELPER_STAGE n=[1-3]|V688_SI_SECOND_INVALID reason=[0-5] stage=[0-4] trace=[0-8]|V688_SI_SECOND_CALL ordinal=[0-9]{1,2} kind=[1-2]|V688_SI_SECOND_STAGE n=[1-3]|V688_SI_SECOND_ACK n=1|V693_SI_NESTED_INVALID reason=[0-5] stage=[0-4] trace=[0-8]|V693_SI_NESTED_CALL ordinal=[0-9]{1,2} kind=[1-2]|V693_SI_NESTED_STAGE n=[1-3]|V693_SI_NESTED_ACK n=1|V697_SI_READ_INVALID trace=[0-8]|V697_SI_ACCESS_INVALID width=[1248] integer=[01]|V667_SI_DISPATCH_INVALID reason=[1-6] stage=[0-6]|V663_EXTERNAL_INVALID reason=[1-9] stage=[0-6]|V663_EXTERNAL_PENDING active=[0-9]{1,10}|V670_VECTOR_REFUSAL mask=[0-9]{1,4}|V678_DISPATCH_REFUSAL mask=[0-9]{1,3} gpr_mask=[0-9]{1,10}',l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
