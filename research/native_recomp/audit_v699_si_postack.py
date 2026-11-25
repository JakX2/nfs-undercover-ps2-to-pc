#!/usr/bin/env python3
"""Require the verified ACK prefix followed by the bounded original ABI return."""
import argparse,re
from pathlib import Path
from audit_v672_si_ack_route import inspect as inspect_ack,RESULT,MARKERS,MAX_LOG
STAGE=b'V699_POSTACK_STAGE n=1'
END=b'V699_POSTACK_RESULT second_return=1 abi=1 original_ack=1 rfi_return=0 boot_verified=0'
PREFIX=b'V699_POSTACK_'
NESTED=[f'V693_SI_NESTED_STAGE n={i}'.encode() for i in range(1,4)]
RETURN=b'V688_SI_SECOND_STAGE n=3'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[r for r in raw.splitlines() if r.startswith(MARKERS+(PREFIX,))]
    i=rows.index(RESULT) if rows.count(RESULT)==1 else -1
    ack=False
    if i>=0 and i>=2 and rows[i-2]==b'V688_SI_SECOND_ACK n=1':
        _,ack=inspect_ack(b'\n'.join(rows[:i+1]),0)
    tail=rows[i+1:] if i>=0 else rows
    ok=bool(ack and rc==0 and tail in ([STAGE,RETURN,END],[STAGE,*NESTED,RETURN,END]))
    return f'V699_POSTACK_CENSUS rc={rc} ack={int(ack)} continued={int(bool(tail and tail[0]==STAGE))} nested_stages={sum(r in tail for r in NESTED)} second_return={int(RETURN in tail)} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V699_POSTACK_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V699_POSTACK_STAGE n=1|V699_POSTACK_INVALID reason=[1-2] trace=[0-9]|V688_SI_SECOND_INVALID reason=[0-5] stage=[0-4] trace=[0-9]{1,2}|V688_SI_SECOND_CALL ordinal=[0-9]{1,2} kind=[1-2]|V693_SI_NESTED_STAGE n=[1-3]|V693_SI_NESTED_INVALID reason=[0-5] stage=[0-4] trace=[0-9]{1,2}|V693_SI_NESTED_CALL ordinal=[0-9]{1,2} kind=[1-2]|V677_SI_ACK_WRITE_INVALID trace=[0-9]{1,2}|V697_SI_READ_INVALID trace=[0-9]{1,2}|V697_SI_ACCESS_INVALID width=[1248] integer=[01]',l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
