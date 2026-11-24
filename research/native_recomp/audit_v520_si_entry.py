#!/usr/bin/env python3
import argparse
from pathlib import Path
from audit_v510_exi_absent import PREFIX,MARK,HW,ARENA,IPC,VECTOR,PACK,ALARM,IRQ,MMIO,RETURN,CONTEXT,REUSE,POLL,HANDLERS,ID,ABSENT,MAX_LOG,inspect as inspect_absent
SI=b'V520_SI_ENTRY_'
STAGES=[f'V520_SI_ENTRY_STAGE n={i}'.encode() for i in range(1,7)]
RESULT=b'V520_SI_ENTRY_RESULT exi_return=1 version_tails=2 slots=4 rate_entry=1 fallback=0 boot_verified=0'
MARKERS=PREFIX+(MARK,HW,ARENA,IPC,VECTOR,PACK,ALARM,IRQ,MMIO,RETURN,CONTEXT,REUSE,POLL,HANDLERS,ID,ABSENT,SI)
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(MARKERS)]
    i=next((i for i,l in enumerate(lines) if l.startswith(SI)),len(lines))
    _,prior=inspect_absent(b'\n'.join(lines[:i]),0);tail=lines[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V520_SI_ENTRY_CENSUS rc={rc} absent={int(prior)} stages={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V520_SI_ENTRY_AUDIT inspected=0');return 1
    print(row);print('V520_SI_ENTRY_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
