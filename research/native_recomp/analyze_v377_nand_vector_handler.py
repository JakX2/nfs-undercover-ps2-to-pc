#!/usr/bin/env python3
"""V377 verify only bounded public markers from native original NAND IRQ run."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

VECTOR=re.compile(r'^V377_NAND_VECTOR_ENTRY saved=([01]) regs=([01]) bytes=([01]) masked=([01]) pending=([01])$')
HANDLER=re.compile(r'^V377_NAND_HANDLER_ENTRY vector=([01]) index=([01]) frame=([01]) saved=([01]) masked=([01]) y1=([01]) advanced=([01])$')
TRIAL=re.compile(r'^V377_NAND_HANDLER_TRIAL stopped=([01]) vector=([01]) handler=([01]) completed=([01])$')

def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    vectors=handlers=trials=0
    vector_ok=handler_ok=trial_ok=0
    for line in lines:
        m=VECTOR.fullmatch(line)
        if m:
            if vectors>=16:break
            vectors+=1;vector_ok|=int(all(v=='1' for v in m.groups()))
            continue
        m=HANDLER.fullmatch(line)
        if m:
            if handlers>=16 or handlers>=vectors:break
            handlers+=1;handler_ok|=int(all(v=='1' for v in m.groups()))
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=16 or trials>=handlers:break
            trials+=1;trial_ok|=int(all(v=='1' for v in m.groups()))
    verified=int(vectors>0 and vectors==handlers==trials and
                 vector_ok and handler_ok and trial_ok)
    return (
        f'V377_NAND_HANDLER_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'vectors={vectors} handlers={handlers} trials={trials} '
        f'vector_any={int(bool(vector_ok))} handler_any={int(bool(handler_ok))} '
        f'trial_any={int(bool(trial_ok))} chain_verified={verified}'
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_native_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    args=p.parse_args()
    try:print(inspect(args.private_native_log,args.native_exit_code))
    except (OSError,ValueError):
        print('V377_NAND_HANDLER_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V377_NAND_HANDLER_AUDIT verified=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
