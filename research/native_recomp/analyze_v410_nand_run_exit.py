#!/usr/bin/env python3
"""V410 original AOT 96-call native run exit, before immutable V390 check.

Reports bounded guest-call counts and CPU flag categories, not original
PowerPC addresses, instructions, registers or private file contents.
No assertion is bypassed, no guest state is changed, and no boot is claimed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,size_band
from scan_original_guest_markers import scan_original_guest_markers

ENTRY=re.compile(
    r'^V410_NAND_GUEST_RUN_EXIT calls=([0-9]|[1-9][0-9]) '
    r'kind=([0-2]) running=([01]) mapped=([01]) '
    r'matched_stop=([01]) v390=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,))
    entries=last=max_calls=stops=running=mapped=old_v390=0
    valid=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if not m:
            continue
        if entries>=16:
            valid=False
            break
        calls,kind,is_running,is_mapped,stop,early=map(int,m.groups())
        valid=valid and bool((not stop or kind!=0) and
                             (not early or kind!=0) and
                             calls<=96)
        entries+=1
        last=calls
        max_calls=max(max_calls,calls)
        stops+=stop
        running+=is_running
        mapped+=is_mapped
        old_v390+=early
    valid=bool(valid and not overflow and entries>0)
    return (
        f'V410_NAND_GUEST_RUN_EXIT_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} max_calls={max_calls} last_calls={last} '
        f'guest_stop_trials={stops} running_trials={running} '
        f'mapped_trials={mapped} v390_trials={old_v390} '
        f'classified={int(valid)} boot_verified=0'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('owner_private_native_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.owner_private_native_log,a.native_exit_code))
    except (OSError,ValueError):
        print('V410_NAND_GUEST_RUN_EXIT_AUDIT inspected=0',file=sys.stderr)
        return 1
    print('V410_NAND_GUEST_RUN_EXIT_AUDIT inspected=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
