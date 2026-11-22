#!/usr/bin/env python3
"""V294: sanitized AOT coverage validation after owner-private NAND restoration.

Consumes only V292's already-sanitized audit lines. A nonmatching
original DOL, missing original function, untranslated entry, missing
dispatcher or unmapped BL is a hard failure. Does not expose original
PowerPC words or generated game C++.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

ROOT=re.compile(
    r"^V292_AOT_REACH owner=1 fixture=1 targets=4 "
    r"child_original=([01]) source_original=([01]) "
    r"child_aot=([01]) source_aot=([01]) child_bl=([01]) "
    r"unmapped_bl=([01]) direct_emit=([01])$"
)
TARGET=re.compile(
    r"^V292_AOT_TARGET pc=([0-9a-f]{8}) words=([0-9]{1,4}) "
    r"present=([01]) same=([0-9]{1,4}) nop=([0-9]{1,4}) "
    r"blr=([0-9]{1,4}) other=([0-9]{1,4}) "
    r"emitted=([01]) dispatch=([01])$"
)
SIZES={
    "8052fa60":52,
    "8051d20c":30,
    "8051e150":34,
    "8052fca4":79,
}

def inspect(data:str)->tuple[str,bool]:
    roots=[m for line in data.splitlines() if (m:=ROOT.fullmatch(line))]
    spans=[m for line in data.splitlines() if (m:=TARGET.fullmatch(line))]
    if len(roots)!=1 or len(spans)!=4:
        raise ValueError("audit_rows")
    distinct={m.group(1) for m in spans}
    if distinct!=set(SIZES):raise ValueError("audit_targets")
    root=tuple(map(int,roots[0].groups()))
    same=compiled=dispatch=0
    for m in spans:
        pc,words,present,matched,nop,blr,other,emitted,routed=m.groups()
        w=int(words)
        if w!=SIZES[pc] or int(present)!=1:
            raise ValueError("span_geometry")
        exact=int(matched)==w and all(
            int(z)==0 for z in (nop,blr,other))
        same+=int(exact)
        compiled+=int(emitted)
        dispatch+=int(routed)
    child_original,source_original,child_aot,source_aot,child_bl,unmapped,direct=root
    ready=(same==4 and compiled==4 and dispatch==4 and
           child_original==source_original==child_aot==source_aot==1 and
           child_bl==direct==1 and unmapped==0)
    summary=(
        f"V294_AOT_COVERAGE targets=4 exact={same} bodies={compiled} "
        f"dispatch={dispatch} child_original={child_original} "
        f"source_original={source_original} child_bl={child_bl} "
        f"unmapped={unmapped} direct_emit={direct} ready={int(ready)}"
    )
    return summary,ready

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("sanitized_owner_report",type=Path)
    a=p.parse_args()
    try: msg,ready=inspect(a.sanitized_owner_report.read_text(
        encoding="utf-8",errors="replace"))
    except (OSError,ValueError):
        print("V294_COVERAGE_AUDIT verified=0",file=sys.stderr)
        return 1
    print(msg)
    print(f"V294_COVERAGE_AUDIT verified={int(ready)}")
    return 0 if ready else 1

if __name__=="__main__":
    sys.exit(main())
