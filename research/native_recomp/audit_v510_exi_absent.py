#!/usr/bin/env python3
import argparse
from pathlib import Path
from audit_v504_exi_id import PREFIX,MARK,HW,ARENA,IPC,VECTOR,PACK,ALARM,IRQ,MMIO,RETURN,CONTEXT,REUSE,POLL,HANDLERS,ID,MAX_LOG,inspect as inspect_id
ABSENT=b'V510_EXI_ABSENT_'
STAGES=[f'V510_EXI_ABSENT_STAGE n={i}'.encode() for i in range(1,9)]
RESULT=b'V510_EXI_ABSENT_RESULT cards=2 absent=1 extra_transfers=0 version_entry=1 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX+(MARK,HW,ARENA,IPC,VECTOR,PACK,ALARM,IRQ,MMIO,RETURN,CONTEXT,REUSE,POLL,HANDLERS,ID,ABSENT))]
    i=next((i for i,l in enumerate(lines) if l.startswith(ABSENT)),len(lines))
    _,prior=inspect_id(b'\n'.join(lines[:i]),0);tail=lines[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V510_EXI_ABSENT_CENSUS rc={rc} id={int(prior)} stages={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V510_EXI_ABSENT_AUDIT inspected=0');return 1
    print(row);print('V510_EXI_ABSENT_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
