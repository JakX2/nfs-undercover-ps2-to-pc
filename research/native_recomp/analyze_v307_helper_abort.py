#!/usr/bin/env python3
"""V307: bounded attribution of the restored NAND helper's native abort.

The original game and complete native trace stay private to the owner CI.
Only public test harness assertion strings may be displayed; unknown
messages are categorized without being copied into GitHub Actions logs.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

from diagnose_v299_native_log import read_edges,category,size_band
from diagnose_v250_native_phase import describe
from analyze_v304_helper_exec import SERVICE
from analyze_v295_restored_native import CALLBACK,CHILD

REPORT=re.compile(
    r"^V250_PUBLIC_FAILURE id=([0-9]{4}) label=([A-Za-z0-9 _.,:/()\-]{1,170}) "
    r"callback=[01] nand=[01] trials=[0-9]{1,2}$"
)
EXCEPTIONS=(
    ("std::runtime_error","runtime"),
    ("std::logic_error","logic"),
    ("std::out_of_range","range"),
    ("std::bad_alloc","alloc")
)

def inspect(private_log:Path, public_harness:str, rc:int)->tuple[str,str]:
    if not public_harness or len(public_harness)>24_000_000:
        raise ValueError("public_catalog")
    kind=category(rc)
    size,lines=read_edges(private_log)
    text="\n".join(lines)
    claim=describe(text,public_harness)
    match=REPORT.fullmatch(claim)
    if match is None:
        raise ValueError("public_result")
    ident=int(match.group(1))
    callback=int(any(CALLBACK.fullmatch(x) for x in lines))
    child=int(any(CHILD.fullmatch(x) for x in lines))
    early=int(any(
        (m:=SERVICE.fullmatch(x)) and m.group(1)=="1"
        for x in lines
    ))
    exception=next((v for k,v in EXCEPTIONS if k in text),"unclassified")
    summary=(
        f"V307_ABORT_PROVENANCE rc={rc} kind={kind} "
        f"size_band={size_band(size)} callback={callback} child={child} "
        f"early={early} public_id={ident:04d} known={int(ident>0)} "
        f"exception={exception}"
    )
    return summary,claim

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("compiled_public_harness",type=Path)
    p.add_argument("native_exit",type=int)
    a=p.parse_args()
    try:
        summary,public=inspect(
            a.private_native_log,
            a.compiled_public_harness.read_text(encoding="utf-8",errors="replace"),
            a.native_exit
        )
    except (OSError,ValueError):
        print("V307_ABORT_AUDIT verified=0",file=sys.stderr)
        return 1
    print(summary)
    print(public)
    print("V307_ABORT_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
