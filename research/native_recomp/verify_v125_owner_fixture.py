#!/usr/bin/env python3
"""Independently validate the authenticated V125 helper fixture.

Private DOL/fixture bytes and exception messages remain inside the CI runner.
The only public output is a bounded status and a fixed source-only error code.
"""
from __future__ import annotations
from pathlib import Path
import argparse

from make_start_to_sc_helper_v125 import make
from test_v125_sc_helper_geometry import verify
from diagnose_v125_fixture_coverage import inspect

FAILURE_CODES = (
    "V125 fixture header/layout modified",
    "V125 inherited data sections modified",
    "V125 translated text section geometry modified",
    "V125 private helper does not map uniquely",
    "V125 helper fixture overlaps inherited code",
    "V125 fixture differs outside authenticated helper span",
    "V125 original helper has no verified NOP-only fixture range",
    "V125 original Wii SHA-256 validation failed",
    "V125 authentic helper entry missing",
)

def error_code(err: BaseException) -> int:
    # Never log the exception: it could contain private paths or game data.
    return FAILURE_CODES.index(str(err)) + 1 if str(err) in FAILURE_CODES else 0

def check(owner: Path) -> None:
    candidate = make(owner)
    verify(candidate, owner)
    flags = inspect(candidate, owner.read_bytes())
    if flags != {"mapped": 1, "owner": 1, "zero": 0, "nop": 0, "same": 1}:
        raise ValueError("V125 authenticated candidate mismatch")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("authenticated_owner", type=Path)
    args = p.parse_args()
    try:
        check(args.authenticated_owner)
    except Exception as exc:
        print(f"V125_PREFLIGHT result=failed code={error_code(exc):02d}")
        return 1
    print("V125_PREFLIGHT result=verified code=00")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
