#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v672_si_ack_route import inspect as inspect_ack,RESULT,MARKERS as ACK_MARKERS,MAX_LOG
from audit_v699_si_postack import STAGE,END,NESTED,RETURN
MARKERS=ACK_MARKERS+(b'V718_POSTACK_REFUSAL ',b'V719_POSTACK_LOOP_POLL ')
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
    polls=[r for r in tail if r.startswith(b'V719_POSTACK_LOOP_POLL ')]
    expected=[f'V719_POSTACK_LOOP_POLL n={i}'.encode() for i in range(1,len(polls)+1)]
    ok=bool(ack and rc==0 and len(polls)<=8192 and polls==expected and
            tail==[STAGE,*NESTED[:2],*LEAVES,NESTED[2],*expected,RETURN,END])
    return f'V709_OS_LEAF_CENSUS rc={rc} ack={int(ack)} leaf_stages={sum(r in tail for r in LEAVES)} nested_return={int(NESTED[2] in tail)} second_return={int(RETURN in tail)} loop_polls={len(polls)} verified={int(ok)} boot_verified=0',ok
def public_diagnostic(line):
    return re.fullmatch(rb'V709_OS_LEAF_STAGE ordinal=[1-3] n=[1-3]|V709_OS_LEAF_INVALID reason=[1-6] ordinal=[1-4] witness=[0-6] trace=[0-9]{1,2}|V699_POSTACK_INVALID reason=[1-2] trace=[0-9]|V688_SI_SECOND_INVALID reason=[0-6] stage=[0-4] trace=[0-9]{1,2}|V688_SI_SECOND_CALL ordinal=[0-9]{1,2} kind=[1-2]|V693_SI_NESTED_INVALID reason=[0-5] stage=[0-4] trace=[0-9]{1,2}|V693_SI_NESTED_CALL ordinal=[0-9]{1,2} kind=[1-2]|V677_SI_ACK_WRITE_INVALID trace=[0-9]{1,2}|V711_POST_CONTROL kind=[1-3] channel=[0-3] geometry=[01] type=[01] mask=[01] reserved=[01]|V697_SI_READ_INVALID trace=[0-9]{1,2}|V697_SI_ACCESS_INVALID width=[1248] integer=[01]|V672_SI_ACK_INVALID reason=[1-6] trace=[0-9]{1,2}|V673_SI_ACK_CALL ordinal=[0-9]{1,2} kind=[0-2]|V680_SI_HELPER_INVALID reason=[0-5] stage=[0-4]|V667_SI_DISPATCH_INVALID reason=[1-6] stage=[0-6]|V663_EXTERNAL_INVALID reason=[1-9] stage=[0-6]|V718_POSTACK_REFUSAL kind=[12] region=[0-3] backward=[0-2] masked=[01] second=[0-4] nested=[0-4] leaves=[0-3]|V719_POSTACK_LOOP_POLL n=[1-9][0-9]{0,3}',line) is not None

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V709_OS_LEAF_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if public_diagnostic(l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
