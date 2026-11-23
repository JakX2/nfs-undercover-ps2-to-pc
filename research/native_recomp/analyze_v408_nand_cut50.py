#!/usr/bin/env python3
"""V408 bounded synthetic-free original guest stop at call 50."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers

ENTRY=re.compile(r'^V408_NAND_CUT50_STOP calls=([1-9]|[1-4][0-9]|50) '
                 r'owner=([01]) selected_return=([01]) parent_return=([01])$')
TRIAL=re.compile(r'^V408_NAND_CUT50_TRIAL calls=([1-9]|[1-4][0-9]|50) '
                 r'kind=([12]) complete=([01])$')

def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,TRIAL))
    entries=trials=cap50=owners=selected=parent=0
    last_call=last_owned=max_calls=0
    ok=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m:
            if entries!=trials or entries>=16:
                ok=False
                break
            calls,owned,sel,par=map(int,m.groups())
            ok=ok and bool((owned or calls==50) and (not par or sel))
            entries+=1
            owners+=owned
            cap50+=int(calls==50)
            selected+=sel
            parent+=par
            last_call=calls
            last_owned=owned
            max_calls=max(max_calls,calls)
            continue
        m=TRIAL.fullmatch(line)
        if m:
            if trials>=entries or trials>=16:
                ok=False
                break
            calls,kind,complete=map(int,m.groups())
            ok=ok and bool(complete and calls==last_call and
                           kind==(1 if last_owned else 2))
            trials+=1
    verified=bool(rc==0 and ok and not overflow and
                  entries==16 and trials==16)
    return (
        f'V408_NAND_CUT50_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} max_calls={max_calls} '
        f'owner_trials={owners} cap50_trials={cap50} '
        f'selected_return_trials={selected} parent_return_trials={parent} '
        f'full_progress={int(verified)} boot_verified=0'
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original_owner_private_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.original_owner_private_log,a.native_exit_code))
    except (ValueError,OSError):
        print('V408_NAND_CUT50_AUDIT inspected=0',file=sys.stderr)
        return 1
    print('V408_NAND_CUT50_AUDIT inspected=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
