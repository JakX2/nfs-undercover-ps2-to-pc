#!/usr/bin/env python3
"""Fail-closed original-free owner gate for the V396 bounded callback frontier.

The separate, authenticated V310 native binary must exit cleanly and emit
sixteen complete V392-V396 guest-evidence chains. This proves a bounded
successor-call observation, NOT an ISFS callback return or full game boot.
No raw guest addresses, bytes, register values or private log text leave CI.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from analyze_v395_nand_isfs_next import inspect as inspect_v395
from analyze_v396_nand_callback_body import inspect as inspect_v396

CHAIN = (
    "V395_NAND_CHAIN_CENSUS "
    + " ".join(f"v{v}_trials=16" for v in range(392,396))
    + " "
    + " ".join(f"v{v}_all_mask=7" for v in range(392,396))
    + " "
    + " ".join(f"v{v}_first_failed=0" for v in range(392,396))
)
FIELD = re.compile(
    r"^V395_NAND_FIELD_CENSUS entries=16 trials=16 "
    r"entry_any_mask=([0-9A-F]{2}) entry_all_mask=([0-9A-F]{2}) "
    r"trial_any_mask=7 trial_all_mask=7 first_bad=0 order_ok=1$"
)
V395 = re.compile(
    r"^V395_NAND_ISFS_NEXT_CENSUS rc=0 kind=zero size_band=[0-3] "
    r"sample_complete=[01] entries=16 trials=16 mapped_any=1 "
    r"selected_any=1 userdata_any=1 nand_any=[01] next_verified=1$"
)
V396 = re.compile(
    r"^V396_NAND_CB_BODY_CENSUS rc=0 kind=zero size_band=[0-3] "
    r"sample_complete=[01] entries=16 trials=16 "
    r"owner_any=([01]) cap_any=([01]) cache_any=[01] "
    r"context_any=[01] nand_any=[01] state_any_mask=[0-7] "
    r"state_all_mask=[0-7] next_verified=1$"
)

def verify(path: Path, rc: int) -> bool:
    if rc != 0:
        return False
    earlier = inspect_v395(path, rc).splitlines()
    later = inspect_v396(path, rc).splitlines()
    if len(earlier) != 3 or len(later) != 1:
        return False
    if earlier[2] != CHAIN or V395.fullmatch(earlier[0]) is None:
        return False
    fields = FIELD.fullmatch(earlier[1])
    successor = V396.fullmatch(later[0])
    if fields is None or successor is None:
        return False
    entry_or, entry_and = (int(x, 16) for x in fields.groups())
    owner, bounded = (int(x) for x in successor.groups())
    return bool((entry_or & 0x7F) == 0x7F and
                (entry_and & 0x7F) == 0x7F and
                (owner or bounded))

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_original_log", type=Path)
    parser.add_argument("native_exit_code", type=int)
    args = parser.parse_args()
    try:
        passed = verify(args.private_original_log, args.native_exit_code)
    except (OSError, ValueError):
        passed = False
    print(f"V396_OWNER_RESULT_GATE verified={int(passed)}")
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
