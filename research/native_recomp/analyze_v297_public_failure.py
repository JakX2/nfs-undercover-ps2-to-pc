#!/usr/bin/env python3
"""V297: identify the public assertion behind V296's first NAND service abort.

Private native output stays inside the owner runner. The only assertion
label emitted must be independently found in the compiled public C++
harness, sanitized by the existing V250 diagnostic.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v250_native_phase import describe

CHILD = re.compile(
    r"^V289_NAND_ENTRY n=[0-9]{1,4} phase=[01] zero=[01] "
    r"sc=[0-9]{1,3} guest=1 inst=([0-9]{1,18})$"
)
SERVICE = re.compile(
    r"^V296_SERVICE_ENTRY kind=1 guest=1 direct=1 "
    r"inst=([0-9]{1,18})$"
)
PUBLIC = re.compile(
    r"^V250_PUBLIC_FAILURE id=([0-9]{4}) "
    r"label=([A-Za-z0-9 _.,:/()\-]{1,170}) "
    r"callback=[01] nand=[01] trials=[0-9]{1,2}$"
)

def analyze(private_log: str, public_harness: str, status: int) -> tuple[str, str, bool]:
    if not 0 <= status <= 255 or len(private_log) > 8_000_000:
        raise ValueError("invalid_input")
    child = [int(m.group(1)) for line in private_log.splitlines()
             if (m := CHILD.fullmatch(line))]
    service = [int(m.group(1)) for line in private_log.splitlines()
               if (m := SERVICE.fullmatch(line))]
    report = describe(private_log, public_harness)
    found = PUBLIC.fullmatch(report)
    if not found:
        raise ValueError("public_classifier")
    ident, label = found.groups()
    progress = bool(child and service and service[0] >= child[0])
    delta = service[0]-child[0] if progress else 0
    summary = (
        f"V297_ORIGINAL_PROGRESS child={len(child)} early={len(service)} "
        f"delta={delta} ordered={int(progress)} "
        f"abort={int(status == 134)} assertion={ident}"
    )
    return summary, report, progress and int(ident) > 0 and label != "other"

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("compiled_public_harness",type=Path)
    p.add_argument("native_exit",type=int)
    opts = p.parse_args()
    try:
        summary, report, valid = analyze(
            opts.private_native_log.read_text(encoding="utf-8",errors="replace"),
            opts.compiled_public_harness.read_text(encoding="utf-8"),
            opts.native_exit)
    except (OSError,ValueError):
        print("V297_PUBLIC_AUDIT verified=0",file=sys.stderr)
        return 1
    print(summary)
    print(report)
    print(f"V297_PUBLIC_AUDIT verified={int(valid)}")
    return 0 if valid else 1

if __name__ == "__main__":
    sys.exit(main())
