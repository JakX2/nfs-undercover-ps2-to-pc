#!/usr/bin/env python3
"""V298: prove stale SC reply observer no longer aborts restored NAND service."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from classify_v178_native_failure import classify_public

OLD="V178 owner-original SC reply callee differs from V177 proof"
ENTRY=re.compile(r"^V296_SERVICE_ENTRY kind=([12]) guest=1 direct=[01] inst=[0-9]{1,18}$")
CHILD=re.compile(r"^V289_NAND_ENTRY n=[0-9]{1,4} phase=[01] zero=[01] sc=[0-9]{1,3} guest=1 inst=[0-9]{1,18}$")
WRITER=re.compile(r"^V278_FCA4_ENTRY n=[0-9]{1,4} phase=[01] cb=[01] nand=[01] child=[01] sc=[0-9]{1,3} guest=1 inst=[0-9]{1,18}$")

def inspect(log: str, harness: str, rc: int) -> tuple[str, bool]:
    if not 0 <= rc <= 255 or len(log)>8_000_000:
        raise ValueError("invalid_input")
    lines=log.splitlines()
    child=sum(bool(CHILD.fullmatch(x)) for x in lines)
    early=sum(bool((m:=ENTRY.fullmatch(x)) and m.group(1)=="1") for x in lines)
    late=sum(bool((m:=ENTRY.fullmatch(x)) and m.group(1)=="2") for x in lines)
    writer=sum(bool(WRITER.fullmatch(x)) for x in lines)
    old_error=any(x.strip().startswith("what(): ") and
                  x.strip()[8:]==OLD for x in lines)
    assertion=classify_public(harness,log)
    passed=(rc==0)
    summary=(
       f"V298_NATIVE_SCOPE rc={rc} child={child} early={early} "
       f"late={late} writer={writer} old_assert={int(old_error)} "
       f"next_assert={assertion:04d} completed={int(passed)}"
    )
    return summary,bool(child and early and not old_error and rc not in (125,126,127))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_log",type=Path)
    p.add_argument("public_harness",type=Path)
    p.add_argument("rc",type=int)
    a=p.parse_args()
    try:
        msg,ok=inspect(a.private_log.read_text(encoding="utf-8",errors="replace"),
                       a.public_harness.read_text(encoding="utf-8"),a.rc)
    except (OSError,ValueError):
        print("V298_SCOPE_AUDIT verified=0",file=sys.stderr)
        return 1
    print(msg)
    print(f"V298_SCOPE_AUDIT verified={int(ok)}")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())
