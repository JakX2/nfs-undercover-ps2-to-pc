#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v663_external_entry import inspect as prior,MARKERS,EVENTS,RESULT,MAX_LOG
PREFIX=b'V751_CAPTURE_'
CAPTURE=[b'V751_CAPTURE_STAGE n=1',b'V751_CAPTURE_STAGE n=2',b'V751_CAPTURE_RESULT live_snapshot=1 saved_gprs=32 special=6 rfi_return=0 boot_verified=0']
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS+(PREFIX,))]
    _,ok=prior(b'\n'.join(l for l in rows if not l.startswith(PREFIX)),rc)
    expected=EVENTS[:2]+CAPTURE[:1]+EVENTS[2:]+CAPTURE[1:]+[RESULT]
    i=rows.index(EVENTS[0]) if rows.count(EVENTS[0])==1 else -1
    ok=bool(ok and i>=0 and rows[i:]==expected and not any(l.startswith(PREFIX) for l in rows[:i]))
    return f'V751_CAPTURE_CENSUS rc={rc} snapshot={int(CAPTURE[0] in rows)} saved_frame={int(CAPTURE[2] in rows)} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V751_CAPTURE_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in CAPTURE or re.fullmatch(rb'V751_CAPTURE_INVALID valid=[01] gprs=[0-9]{1,2} special=[0-9]{1,2}|V663_EXTERNAL_INVALID reason=(?:[1-9]|1[01]) stage=[0-6]',l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
