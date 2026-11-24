#!/usr/bin/env python3
import argparse,re
from pathlib import Path
from audit_v581_dsp_return import MARKERS as PRIOR,MAX_LOG,inspect as inspect_dsp
PREFIX=b'V591_MI_'
MAPPER=b'V620_MI_MAPPER'
MARKERS=PRIOR+(PREFIX,MAPPER)
STAGES=[f'V591_MI_STAGE n={i}'.encode() for i in range(1,21)]
RESULT=b'V591_MI_RESULT handlers=5 shutdown=1 bat=32 rfi_returns=2 mi_mask=16 returned=1 permissions=0 firmware_executed=0 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(rows) if l.startswith(PREFIX)),len(rows))
    _,prior=inspect_dsp(b'\n'.join(rows[:i]),0);tail=rows[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in rows)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback and not any(l.startswith(MAPPER) for l in raw.splitlines()))
    return f'V591_MI_CENSUS rc={rc} dsp={int(prior)} stages={n} permissions=0 fallback={fallback} verified={int(ok)} boot_verified=0',ok
def mapper_diagnostic(raw,rc):
    if rc!=115:return None
    rows=raw.splitlines()
    invalid=[l for l in rows if l.startswith(b'V591_MI_INVALID')]
    found=[l for l in rows if l.startswith(MAPPER)]
    if invalid!=[b'V591_MI_INVALID reason=4 stage=11'] or len(found)!=1:return None
    m=re.fullmatch(rb'V620_MI_MAPPER refusal=([0-9]{1,10}) bat_count=([0-9]{1,10}) msr=([0-9a-f]{1,8})',found[0])
    if not m:return None
    mask,count=int(m[1]),int(m[2])
    if not mask or mask&~0x3fff3fff or count>0xffffffff:return None
    if rows.index(found[0])<=rows.index(invalid[0]):return None
    return found[0].decode('ascii')
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):
        print('V591_MI_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if re.fullmatch(rb'V591_MI_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}|V581_DSP_RETURN_INVALID reason=[0-9]{1,2} stage=[0-9]{1,2}|V581_DSP_PROFILE_INVALID rejected=1',l):
            print(l.decode());break
    for l in raw.splitlines():
        if re.fullmatch(rb'V604_MI_EDGE stage=[0-9]{1,2} pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8} outer=[0-9]{1,2} metadata=[0-9]{1,2}',l):
            print(l.decode());break
    diag=mapper_diagnostic(raw,a.rc)
    if diag:print(diag)
    print(row);print('V591_MI_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
