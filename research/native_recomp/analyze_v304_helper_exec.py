#!/usr/bin/env python3
"""V304: bounded native trial classification for authenticated 41-word helper.

Read only the head and tail of the owner-private trace. Print fixed
categories, bounded counts and verified public guest-entry markers.
A successful diagnostic does not mean the game booted or returned
from its original NAND initialization.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from diagnose_v299_native_log import (
    read_edges, category, size_band, PRIOR_LIMIT
)
from analyze_v295_restored_native import CALLBACK, CHILD, WRITER

SERVICE=re.compile(
    r"^V296_SERVICE_ENTRY kind=([12]) guest=1 direct=[01] "
    r"inst=[0-9]{1,18}$"
)
HOTSPOT=re.compile(
    r"^V(?:98_DEPENDENCY|104_FALLTHROUGH|112_BOUNDARY) "
    r"pc=804f2064(?: |$)"
)

def inspect(log:Path,rc:int)->str:
    kind=category(rc)
    size,lines=read_edges(log)
    services=[m.group(1) for line in lines
              if (m:=SERVICE.fullmatch(line))]
    callback=sum(bool(CALLBACK.fullmatch(line)) for line in lines)
    child=sum(bool(CHILD.fullmatch(line)) for line in lines)
    writer=sum(bool(WRITER.fullmatch(line)) for line in lines)
    repeats=sum(bool(HOTSPOT.match(line)) for line in lines)
    return (
        f"V304_HELPER_NATIVE rc={rc} kind={kind} size_band={size_band(size)} "
        f"over_limit={int(size>PRIOR_LIMIT)} edge_sample=1 "
        f"callback={callback} child={child} early={services.count('1')} "
        f"late={services.count('2')} writer={writer} "
        f"old_hotspot={repeats} completed={int(rc==0)}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        row=inspect(a.private_native_log,a.native_exit)
    except (OSError,ValueError):
        print("V304_EXEC_AUDIT verified=0",file=sys.stderr)
        return 1
    print(row)
    print("V304_EXEC_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
