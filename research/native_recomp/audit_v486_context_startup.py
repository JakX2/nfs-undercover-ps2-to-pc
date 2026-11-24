#!/usr/bin/env python3
import argparse
from pathlib import Path
from audit_v483_irq_return import PREFIX,MARK,HW,ARENA,IPC,VECTOR,PACK,ALARM,IRQ,MMIO,RETURN,MAX_LOG,inspect as inspect_irq
CONTEXT=b'V486_CONTEXT_'
STAGES=[f'V486_CONTEXT_STAGE n={i}'.encode() for i in range(1,5)]
RESULT=b'V486_CONTEXT_RESULT handler=1 current_context=1 cache_entry=1 fallback=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX+(MARK,HW,ARENA,IPC,VECTOR,PACK,ALARM,IRQ,MMIO,RETURN,CONTEXT))]
    i=next((i for i,l in enumerate(lines) if l.startswith(CONTEXT)),len(lines))
    _,prior=inspect_irq(b'\n'.join(lines[:i]),0);tail=lines[i:]
    n=0
    for a,b in zip(tail,STAGES):
        if a!=b:break
        n+=1
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    ok=bool(rc==0 and prior and tail==STAGES+[RESULT] and not fallback)
    return f'V486_CONTEXT_CENSUS rc={rc} irq_return={int(prior)} stages={n} fallback={fallback} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V486_CONTEXT_AUDIT inspected=0');return 1
    print(row);print('V486_CONTEXT_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
