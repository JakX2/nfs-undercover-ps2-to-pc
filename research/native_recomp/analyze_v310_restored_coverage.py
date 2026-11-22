#!/usr/bin/env python3
"""V310: verify original 64-word descendant and unchanged nearby AOT coverage.

Consume only independently authored, sanitized V306 rows produced inside
owner-private CI. Reject an un-restored NOP body, missing native dispatch,
or regression in the two authenticated interior call windows.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

SUMMARY=re.compile(
    r"^V306_COVERAGE owner=1 targets=4 exact=([0-4]) "
    r"interior=([0-4]) emitted=([0-4]) dispatch=([0-4]) "
    r"missing=([0-4]) partial=([0-4]) unknown=([0-4])$"
)
TARGET=re.compile(
    r"^V306_DESCENDANT pc=80519bcc kind=exact base=80519bcc "
    r"offset=0 words=([0-9]{1,4}) present=([01]) same=([0-9]{1,4}) "
    r"nop=([0-9]{1,4}) blr=([0-9]{1,4}) other=([0-9]{1,4}) "
    r"body=([01]) dispatch=([01])$"
)
INTERIOR=re.compile(
    r"^V306_DESCENDANT pc=(80545104|80545150) kind=interior "
    r"base=[0-9a-f]{8} offset=[0-9]{1,4} words=([0-9]{1,4}) "
    r"present=1 same=([0-9]{1,4}) nop=0 blr=0 other=0 "
    r"body=[01] dispatch=[01]$"
)
def inspect(log:str)->tuple[str,bool]:
    summaries=[m for x in log.splitlines() if (m:=SUMMARY.fullmatch(x))]
    targets=[m for x in log.splitlines() if (m:=TARGET.fullmatch(x))]
    interiors=[m for x in log.splitlines() if (m:=INTERIOR.fullmatch(x))]
    if len(summaries)!=1 or len(targets)!=1:
        raise ValueError("sanitized_rows")
    exact,interior,emitted,dispatch,missing,partial,unknown=map(
        int,summaries[0].groups()
    )
    words,present,same,nop,blr,other,body,entry=map(int,targets[0].groups())
    valid_interiors=(
        len(interiors)==2 and
        {m.group(1) for m in interiors}=={"80545104","80545150"} and
        all(int(m.group(2))==int(m.group(3)) and int(m.group(2))>0
            for m in interiors)
    )
    ready=bool(
        (exact,interior,missing,partial,unknown)==(2,2,0,0,0)
        and words==same==64 and present==1
        and nop==blr==other==0 and body==entry==1
        and emitted>=2 and dispatch>=2 and valid_interiors
    )
    report=(
        f"V310_NATIVE_COVERAGE source=1 words={words} original={int(same==64)} "
        f"body={body} dispatch={entry} interiors={int(valid_interiors)} "
        f"ready={int(ready)}"
    )
    return report,ready

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_sanitized_coverage",type=Path)
    a=p.parse_args()
    try:
        report,valid=inspect(a.private_sanitized_coverage.read_text(
            encoding="utf-8",errors="replace"))
    except (OSError,ValueError):
        print("V310_COVERAGE_AUDIT verified=0",file=sys.stderr)
        return 1
    print(report)
    print(f"V310_COVERAGE_AUDIT verified={int(valid)}")
    return 0 if valid else 1

if __name__=="__main__":
    sys.exit(main())
