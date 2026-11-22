#!/usr/bin/env python3
"""V303: fail-closed sanitized proof of the restored NAND helper AOT candidate.

Consumes exactly one V301 owner-private audit row for the newly restored
fixture. Requires the complete 41-word original body, one native entry,
its dispatcher, and an authentic direct call from the NAND service.
No original instruction words or generated game C++ are printed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

ROW=re.compile(
    r"^V301_HELPER_AOT owner=1 elf=1 pc=804f2064 "
    r"words=([0-9]{1,5}) present=([01]) same=([0-9]{1,5}) "
    r"nop=([0-9]{1,5}) blr=([0-9]{1,5}) other=([0-9]{1,5}) "
    r"body=([01]) dispatch=([01]) caller=([01]) "
    r"unmapped=([01]) direct=([01])$"
)
EXPECTED_WORDS=41

def inspect(output:str)->tuple[str,bool]:
    rows=[m for line in output.splitlines() if (m:=ROW.fullmatch(line))]
    if len(rows)!=1:
        raise ValueError("audit_rows")
    words,present,same,nop,blr,other,body,dispatch,caller,unmapped,direct=(
        map(int,rows[0].groups())
    )
    if words!=EXPECTED_WORDS:
        raise ValueError("symbol_size")
    exact=int(present==1 and same==words and nop==blr==other==0)
    ready=bool(exact and body and dispatch and caller and direct and not unmapped)
    summary=(
        f"V303_AOT_HELPER original={exact} words={words} "
        f"body={body} dispatch={dispatch} caller={caller} "
        f"unmapped={unmapped} direct={direct} ready={int(ready)}"
    )
    return summary,ready

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("sanitized_v301_restored_audit",type=Path)
    a=p.parse_args()
    try:
        message,valid=inspect(
            a.sanitized_v301_restored_audit.read_text(encoding="utf-8",
                                                      errors="replace")
        )
    except (OSError,ValueError):
        print("V303_COVERAGE_AUDIT verified=0",file=sys.stderr)
        return 1
    print(message)
    print(f"V303_COVERAGE_AUDIT verified={int(valid)}")
    return 0 if valid else 1

if __name__=="__main__":
    sys.exit(main())
