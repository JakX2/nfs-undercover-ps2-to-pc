#!/usr/bin/env python3
"""Audit the complete-image MEM2 and IPC-buffer continuation without exposing guest data."""
import argparse
from pathlib import Path
import re
from audit_v444_full_os_arena import PREFIX,MARK,HW,ARENA,inspect as inspect_arena,MAX_LOG
from audit_v439_full_os_hardware import STAGES as HW_STAGES,HEX_STAGES
IPC=b'V446_IPC_'
BEGIN=re.compile(rb'V446_IPC_BEGIN clamp=([01])')
STAGES=[f'V446_IPC_STAGE n={i} valid=1'.encode() for i in range(1,5)]
RESULT=b'V446_IPC_RESULT mem2_stores=2 ipc_stores=2 exception_entry=1 bounds=1 fallback=0 boot_verified=0'
INVALID=re.compile(rb'V446_IPC_INVALID reason=([1-8]) stage=([0-4])')
def legacy_arena_prefix(lines):
    # Diagnostic only. Normalize exactly four historically misformatted
    # records, within the hardware prefix, never arbitrary log text.
    # Re-run the entire canonical ancestor gate on that private copy.
    for upper in (False,True):
        replacements={old.replace(b'n='+format(n,'x').encode(),b'n='+format(n,'X').encode()) if upper else old:new
                      for n,old,new in zip(range(10,14),HEX_STAGES[9:],HW_STAGES[9:])}
        if not all(lines.count(old)==1 for old in replacements):continue
        if any(line in lines for line in HW_STAGES[9:]):continue
        normalized=[replacements.get(line,line) for line in lines]
        if inspect_arena(b'\n'.join(normalized),0)[1]:return True
    return False

def inspect(raw,rc):
    if len(raw)>MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    lines=[l for l in raw.splitlines() if l.startswith(PREFIX+(MARK,HW,ARENA,IPC))]
    i=next((i for i,l in enumerate(lines) if l.startswith(IPC)),len(lines))
    _,prior=inspect_arena(b'\n'.join(lines[:i]),0);tail=lines[i:]
    begin=BEGIN.fullmatch(tail[0]) if tail else None
    count=0
    if begin:
        for a,b in zip(tail[1:],STAGES):
            if a!=b:break
            count+=1
    errors=[m for l in tail if (m:=INVALID.fullmatch(l))]
    reason=int(errors[0][1]) if len(errors)==1 else 0
    fallback=int(b'V425_HARDWARE_FALLBACK hit=1' in lines)
    complete=bool(rc==0 and begin and tail[1:]==STAGES+[RESULT] and not fallback)
    ok=bool(complete and prior)
    terminal=int(tail.count(RESULT)==1)
    legacy=int(bool(complete and not prior and legacy_arena_prefix(lines[:i])))
    return f'V446_IPC_CENSUS rc={rc} arena={int(prior)} stages={count} clamp={int(begin[1]) if begin else 0} fallback={fallback} reason={reason} terminal={terminal} legacy_chain_complete={legacy} verified={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>MAX_LOG:raise ValueError('size')
        row,ok=inspect(a.log.read_bytes(),a.rc)
    except (OSError,ValueError):
        print('V446_IPC_AUDIT inspected=0');return 1
    print(row);print('V446_IPC_AUDIT inspected=1');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
