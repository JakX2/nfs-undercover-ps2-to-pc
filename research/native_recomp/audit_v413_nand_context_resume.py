#!/usr/bin/env python3
"""Strict ordered owner gate for V413, without exporting private guest state."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from scan_original_guest_markers import scan_original_guest_markers

RETIRED=re.compile(r'V412_LEGACY_FRONTIER continued=1')
PREFIX=re.compile(r'V413_CONTEXT_PREFIX verified=([01])')
LOAD=re.compile(r'V413_CONTEXT_LOAD mapped=([01])')
RESTORE=re.compile(r'V413_CONTEXT_RESTORE regs=([01]) msr=([01]) coherent=([01]) interrupted=([01])')
EXIT=re.compile(r'V413_CONTEXT_EXIT calls=([0-9]{1,3}) prefix=([01]) load=([01]) mapped=([01]) hit=([01]) restored=([01]) interrupted=([01]) matched=([01])')
TRIAL=re.compile(r'V413_CONTEXT_TRIAL complete=([01])')
PATTERNS=(RETIRED,PREFIX,LOAD,RESTORE,EXIT,TRIAL)

def inspect(path:Path,rc:int)->str:
    _,lines,overflow=scan_original_guest_markers(path,PATTERNS)
    retired=prefixes=loads=hits=restored=interrupted=trials=0
    max_calls=0
    valid=not overflow
    retired_seen=False; prefix=None; load=None; restore=None; exit_seen=False
    for line in lines:
        if RETIRED.fullmatch(line):
            if retired_seen or exit_seen:valid=False
            retired_seen=True
            retired+=1
        elif (m:=PREFIX.fullmatch(line)):
            if not retired_seen or prefix is not None or exit_seen:valid=False
            prefix=int(m[1]);prefixes+=prefix
        elif (m:=LOAD.fullmatch(line)):
            # The scheduler can select a context before the 50-call retirement.
            if load is not None or exit_seen:valid=False
            load=int(m[1]);loads+=1
        elif (m:=RESTORE.fullmatch(line)):
            if load!=1 or restore is not None or exit_seen:valid=False
            restore=tuple(map(int,m.groups()));hits+=1
        elif (m:=EXIT.fullmatch(line)):
            calls,p,l,mp,h,rs,it,matched=map(int,m.groups())
            max_calls=max(max_calls,calls)
            expected=int(restore is not None and all(restore[:3]))
            if (not retired_seen or exit_seen or calls!=192 or prefix!=1 or p!=1 or
                l!=int(load is not None) or mp!=(load or 0) or h!=int(restore is not None) or
                rs!=expected or (restore is not None and it!=restore[3]) or
                (it and not mp) or matched!=1):valid=False
            restored+=rs;interrupted+=int(bool(rs and it));exit_seen=True
        elif (m:=TRIAL.fullmatch(line)):
            if not retired_seen or not exit_seen or m[1]!='1':valid=False
            trials+=1;retired_seen=False;prefix=load=restore=None;exit_seen=False
    verified=bool(rc==0 and valid and not retired_seen and load is None and restore is None and retired==prefixes==trials==16)
    return (f'V413_CONTEXT_CENSUS rc={rc} retired={retired} prefix96={prefixes} '
            f'loads={loads} hits={hits} restored={restored} interrupted={interrupted} '
            f'trials={trials} max_calls={max_calls} verified={int(verified)} '
            f'context_verified={int(verified and restored==16)} '
            f'interrupted_verified={int(verified and interrupted==16)} boot_verified=0')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('log',type=Path);p.add_argument('rc',type=int)
    a=p.parse_args()
    try:print(inspect(a.log,a.rc))
    except (OSError,ValueError):return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
