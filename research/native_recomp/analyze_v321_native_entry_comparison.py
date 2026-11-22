#!/usr/bin/env python3
"""V321: bounded private AOT entry comparison for V304 and V310 trials.

Only exact one-shot original-free instrumentation markers are accepted.
The output is a bounded 8-bit entry mask; it never includes original
guest instruction bytes, raw logs, generated C++ or private paths.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from derive_v321_guest_entry_probe import TARGETS
from diagnose_v299_native_log import WINDOW,read_edges

ENTRY=re.compile(r"^V321_GUEST_ENTRY pc=([0-9a-f]{8})$")

def summarize(path:Path)->tuple[int,int]:
    size,lines=read_edges(path)
    found=0
    by_pc={pc:i for i,pc in enumerate(TARGETS)}
    for line in lines:
        m=ENTRY.fullmatch(line)
        if m is None:
            continue
        bit=by_pc.get(int(m.group(1),16))
        if bit is not None:
            found|=1<<bit
    return found,int(size<=WINDOW)

def compare(base:Path, restored:Path)->str:
    bmask,bcomplete=summarize(base)
    rmask,rcomplete=summarize(restored)
    return (
        f"V321_ENTRY_COMPARISON targets={len(TARGETS)} "
        f"base_mask={bmask:02x} restored_mask={rmask:02x} "
        f"added_mask={(rmask&~bmask):02x} lost_mask={(bmask&~rmask):02x} "
        f"base_complete={bcomplete} restored_complete={rcomplete}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_v304_log",type=Path)
    p.add_argument("private_v310_log",type=Path)
    a=p.parse_args()
    try:
        line=compare(a.private_v304_log,a.private_v310_log)
    except (OSError,ValueError):
        print("V321_ENTRY_AUDIT verified=0",file=sys.stderr)
        return 1
    print(line)
    print("V321_ENTRY_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
