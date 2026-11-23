#!/usr/bin/env python3
"""V362: prove a completed bounded owner-native harness independently of rc=0.

A normally returning process is NOT a completed Wii startup, original main,
IOS ACK or a PASS in the bounded V77-derived test. Require the existing
original-free, exact owner 16-trial PASS marker before reporting success.
Inspect only bounded private log edges, never print source paths or guest data.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

from diagnose_v299_native_log import WINDOW,category,read_edges,size_band

PASS=re.compile(
    r"^PASS: ([1-9][0-9]{0,11}) V77 recovered continuous original "
    r"__start->ACK return and IOS reply assertions; "
    r"mode=(owner|synthetic) trials=([0-9]{1,3}) "
    r"stop=0x[0-9a-f]{8}$"
)

def inspect(path:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(path)
    owner=0
    synthetic=0
    exact=0
    for line in lines:
        m=PASS.fullmatch(line)
        if m is None:
            continue
        checks,mode,trials=m.groups()
        if mode=="owner" and int(trials)==16:
            owner=1
            exact=int(rc==0)
        if mode=="synthetic":
            synthetic=1
    return (
        f"V362_BOUNDED_EXIT rc={rc} kind={kind} size_band={size_band(size)} "
        f"sample_complete={int(size<=WINDOW)} owner_pass={owner} "
        f"synthetic_pass={synthetic} harness_complete={exact} "
        f"game_boot=0"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        report=inspect(a.private_native_log,a.native_exit)
    except (OSError,ValueError):
        print("V362_EXIT_AUDIT verified=0",file=sys.stderr)
        return 1
    print(report)
    print("V362_EXIT_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
