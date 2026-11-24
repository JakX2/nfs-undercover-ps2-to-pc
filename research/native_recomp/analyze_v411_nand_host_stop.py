#!/usr/bin/env python3
"""Bounded host-stop event census, with no guest source/address disclosure."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from diagnose_v299_native_log import category,size_band
from scan_original_guest_markers import scan_original_guest_markers
ENTRY=re.compile(r'^V411_HOST_STOP event=([1-8]) site=([1-9][0-9]{0,3}) throws=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,))
    n=first=last=throws=0
    good=True
    for line in lines:
        m=ENTRY.fullmatch(line)
        if not m:continue
        seq,site,adjacent=map(int,m.groups())
        if seq!=n+1 or n>=8:
            good=False
            break
        n+=1
        if n==1:first=site
        last=site
        throws+=adjacent
    return (f'V411_HOST_STOP_CENSUS rc={rc} kind={category(rc)} size_band={size_band(size)} '
            f'events={n} first_site={first} last_site={last} adjacent_throw={throws} '
            f'classified={int(not overflow and good and n>0)} boot_verified=0')
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('log',type=Path)
    p.add_argument('rc',type=int)
    a=p.parse_args()
    try:print(inspect(a.log,a.rc))
    except (ValueError,OSError):
        print('V411_HOST_STOP_AUDIT inspected=0')
        return 1
    print('V411_HOST_STOP_AUDIT inspected=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
