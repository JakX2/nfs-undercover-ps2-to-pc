#!/usr/bin/env python3
"""Fail closed on missing, duplicate, foreign or reordered startup evidence."""
import argparse,re
from pathlib import Path
from audit_v591_memory_init import MARKERS as PRIOR,MAX_LOG,inspect as inspect_mi
PREFIX=b'V603_REPORT_'
MARKERS=PRIOR+(PREFIX,)
BEGIN=b'V603_REPORT_BEGIN native=1'
RESULT=re.compile(rb'V603_REPORT_RESULT reports=10 getters=6 native_console=1 computed=([01]) returned=1 output_backend=0 fallback=0 boot_verified=0')
EVENTS=[BEGIN]+[f'V603_REPORT_CALL n={i}'.encode() for i in range(1,7)]
for i in range(3):
    EVENTS.extend((f'V603_REPORT_GETTER n={2*i+1}'.encode(),f'V603_REPORT_GETTER n={2*i+2}'.encode(),f'V603_REPORT_CALL n={7+i}'.encode()))
EVENTS.append(b'V603_REPORT_CALL n=10')
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(rows) if l.startswith(PREFIX)),len(rows))
    _,prior=inspect_mi(b'\n'.join(rows[:i]),0);tail=rows[i:]
    n=0
    for a,b in zip(tail,EVENTS):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in rows)
    ok=bool(rc==0 and prior and len(tail)==len(EVENTS)+1 and n==len(EVENTS) and RESULT.fullmatch(tail[-1]) and not fallback)
    return f'V603_REPORT_CENSUS rc={rc} mi={int(prior)} events={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V603_REPORT_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V603_REPORT_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2} reports=[0-9]{1,2} getters=[0-9]{1,2}|V591_MI_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}',l):
            print(l.decode());break
    print(row);print('V603_REPORT_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
