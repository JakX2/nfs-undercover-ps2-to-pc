#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v672_si_ack_route import inspect as inspect_ack,RESULT,MARKERS,MAX_LOG
from audit_v699_si_postack import STAGE,END,NESTED,RETURN
LEAVES=[f'V709_OS_LEAF_STAGE ordinal={i} n={j}'.encode() for i in range(1,4) for j in range(1,4)]
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[r for r in raw.splitlines() if r.startswith(MARKERS)]
    i=rows.index(RESULT) if rows.count(RESULT)==1 else -1
    ack=False
    if i>=2 and rows[i-2]==b'V688_SI_SECOND_ACK n=1':_,ack=inspect_ack(b'\n'.join(rows[:i+1]),0)
    tail=rows[i+1:] if i>=0 else rows
    # Some original paths may return without entering the nested helper.
    # Such a path is not a successful three-leaf execution.
    ok=bool(ack and rc==0 and tail==[STAGE,*NESTED[:2],*LEAVES,NESTED[2],RETURN,END])
    return f'V709_OS_LEAF_CENSUS rc={rc} ack={int(ack)} leaf_stages={sum(r in tail for r in LEAVES)} nested_return={int(NESTED[2] in tail)} second_return={int(RETURN in tail)} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V709_OS_LEAF_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V709_OS_LEAF_STAGE ordinal=[1-3] n=[1-3]|V709_OS_LEAF_INVALID reason=[1-5] ordinal=[1-4] witness=[0-6] trace=[0-9]{1,2}|V699_POSTACK_INVALID reason=[1-2] trace=[0-9]|V688_SI_SECOND_INVALID reason=[0-5] stage=[0-4] trace=[0-9]{1,2}|V688_SI_SECOND_CALL ordinal=[0-9]{1,2} kind=[1-2]|V693_SI_NESTED_INVALID reason=[0-5] stage=[0-4] trace=[0-9]{1,2}|V693_SI_NESTED_CALL ordinal=[0-9]{1,2} kind=[1-2]|V677_SI_ACK_WRITE_INVALID trace=[0-9]{1,2}|V697_SI_READ_INVALID trace=[0-9]{1,2}|V697_SI_ACCESS_INVALID width=[1248] integer=[01]',l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
