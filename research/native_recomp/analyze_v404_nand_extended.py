#!/usr/bin/env python3
"""V404 bounded 96-call authentic guest candidate outcome, never boot proof.

This is a SEPARATE owner-private native execution with the original AOT.
A failure/timeout remains diagnostic and cannot invalidate the already
verified V403 24-call and V402 48-call controls.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers

ENTRY=re.compile(
    r'^V404_NAND_EXTENDED_STOP calls=([1-9]|[1-8][0-9]|9[0-6]) '
    r'owner=([01]) selected_return=([01]) parent_return=([01])$')
TRIAL=re.compile(
    r'^V404_NAND_EXTENDED_TRIAL calls=([1-9]|[1-8][0-9]|9[0-6]) '
    r'kind=([12]) complete=([01])$')

def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,TRIAL))
    entries=trials=owners=cap96=selected=parent=0
    max_calls=0
    good=True
    last_call=last_owner=0
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:
                good=False
                break
            calls,owner,sel,par=map(int,m.groups())
            good=good and bool((owner or calls==96) and
                               (not par or sel))
            entries+=1
            owners+=owner
            cap96+=int(calls==96)
            selected+=sel
            parent+=par
            max_calls=max(max_calls,calls)
            last_call=calls
            last_owner=owner
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if entries<=trials or trials>=16:
                good=False
                break
            calls,kind,completed=map(int,m.groups())
            good=good and bool(calls==last_call and completed and
                               kind==(1 if last_owner else 2))
            trials+=1
    verified=bool(not overflow and good and
                  rc==0 and entries==16 and trials==16)
    return (
        f'V404_NAND_EXTENDED_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} max_calls={max_calls} '
        f'owner_trials={owners} cap96_trials={cap96} '
        f'selected_return_trials={selected} parent_return_trials={parent} '
        f'full_progress={int(verified)} boot_verified=0'
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    args=p.parse_args()
    try:
        print(inspect(args.private_original_log,args.native_exit_code))
    except (ValueError,OSError):
        print('V404_NAND_EXTENDED_AUDIT inspected=0',file=sys.stderr)
        return 1
    print('V404_NAND_EXTENDED_AUDIT inspected=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
