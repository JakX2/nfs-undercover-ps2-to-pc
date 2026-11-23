#!/usr/bin/env python3
"""V375 bounded public Y1 exception-boundary census with no game data."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

PAT=re.compile(
    r'^V375_NAND_Y1_BOUNDARY n=([1-9]|1[0-9]|2[0-4]) '
    r'call=([01]) running=([01]) dispatch=([01]) aligned=([01]) '
    r'mode=([01]) ee=([01]) installed=([01]) preemptible=([01]) '
    r'site=([123]) drained=([01])$'
)

def inspect(path:Path,rc:int)->str:
    size,lines=read_edges(path)
    count=first=call_any=running_any=free_any=aligned_any=mode_any=installed_any=0
    preemptible_any=drained_any=site_mask=0
    for line in lines:
        m=PAT.fullmatch(line)
        if not m:continue
        n,call,running,free,aligned,mode,ee,installed,preemptible,site,drained=map(
            int,m.groups())
        expected=call and running and free and aligned and mode and ee and installed
        if n!=count+1 or preemptible!=int(bool(expected)) or not ee:
            break
        count+=1
        if preemptible and not first:
            first=count
        call_any|=call
        running_any|=running
        free_any|=free
        aligned_any|=aligned
        mode_any|=mode
        installed_any|=installed
        preemptible_any|=preemptible
        drained_any|=drained
        site_mask|=1<<(site-1)
    return (
        f'V375_Y1_BOUNDARY_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'samples={count} first_preemptible={first} '
        f'call_any={call_any} running_any={running_any} '
        f'free_any={free_any} aligned_any={aligned_any} mode_any={mode_any} '
        f'installed_any={installed_any} preemptible_any={preemptible_any} '
        f'drained_any={drained_any} site_mask={site_mask:01x}'
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('owner_private_log',type=Path)
    p.add_argument('native_exit',type=int)
    args=p.parse_args()
    try:
        print(inspect(args.owner_private_log,args.native_exit))
    except (OSError,ValueError):
        print('V375_Y1_BOUNDARY_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V375_Y1_BOUNDARY_AUDIT verified=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
