#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v603_boot_report import MARKERS as PRIOR,MAX_LOG,inspect as inspect_report
PREFIX=b'V609_ARENA_'
MARKERS=PRIOR+(PREFIX,)
EVENTS=[]
for n in range(1,21):
    EVENTS.append(f'V609_ARENA_STAGE n={n}'.encode())
    if n in (9,18):
        lane=1 if n==9 else 2
        EVENTS.extend((f'V609_ARENA_VECTOR lane={lane}'.encode(),f'V609_ARENA_SC lane={lane}'.encode()))
RESULT=re.compile(rb'V609_ARENA_RESULT lanes=2 reset=2 getters=6 zeros=([0-9]{1,7}) flush=16384 vectors=2 returned=1 hardware_cache=0 fallback=0 boot_verified=0')
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(rows) if l.startswith(PREFIX)),len(rows))
    _,prior=inspect_report(b'\n'.join(rows[:i]),0);tail=rows[i:]
    n=0
    for a,b in zip(tail,EVENTS):
        if a!=b:break
        n+=1
    m=RESULT.fullmatch(tail[-1]) if tail else None
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in rows)
    ok=bool(rc==0 and prior and len(tail)==len(EVENTS)+1 and n==len(EVENTS) and m and 16384<=int(m[1])<2883584 and not fallback)
    return f'V609_ARENA_CENSUS rc={rc} report={int(prior)} events={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V609_ARENA_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V609_ARENA_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}|V609_ARENA_SC_INVALID rejected=1|V603_REPORT_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2} reports=[0-9]{1,2} getters=[0-9]{1,2}|V591_MI_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}',l):
            print(l.decode());break
    print(row);print('V609_ARENA_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
