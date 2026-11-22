#!/usr/bin/env python3
"""V296: classify bounded original NAND abort without revealing owner logs.

Never print raw native stderr, runtime messages or proprietary text.
Only fixed categories, counts and source-owned public assertion indices.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from classify_v178_native_failure import classify_public

SERVICE = re.compile(
    r"^V296_SERVICE_ENTRY kind=([12]) guest=([01]) direct=([01]) "
    r"inst=([0-9]{1,18})$"
)
CHILD = re.compile(
    r"^V289_NAND_ENTRY n=[0-9]{1,4} phase=[01] zero=[01] "
    r"sc=[0-9]{1,3} guest=1 inst=[0-9]{1,18}$"
)
EXCEPTIONS = (
    ("std::runtime_error", "runtime_error"),
    ("std::out_of_range", "out_of_range"),
    ("std::invalid_argument", "invalid_argument"),
    ("std::bad_alloc", "bad_alloc"),
    ("std::logic_error", "logic_error"),
)
def classify(log: str, harness: str, status: int) -> tuple[str, bool]:
    if not 0 <= status <= 255 or len(log) > 8_000_000:
        raise ValueError("invalid_native_input")
    events = [m for line in log.splitlines()
              if (m := SERVICE.fullmatch(line))]
    original = sum(bool(CHILD.fullmatch(line)) for line in log.splitlines())
    early = sum(m.group(1) == "1" for m in events)
    late = sum(m.group(1) == "2" for m in events)
    direct = sum(m.group(3) == "1" for m in events)
    valid = all(m.group(2) == "1" for m in events)
    assertion = classify_public(harness, log)
    exception = next((label for needle, label in EXCEPTIONS if needle in log),
                     "unclassified")
    reported = (
        f"V296_NATIVE_FRONTIER rc={status} child={original} early={early} "
        f"late={late} direct={direct} assertion={assertion:04d} "
        f"exception={exception} original_guest={int(valid)}"
    )
    return reported, bool(original and valid and status not in (125, 126, 127))

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_private_log", type=Path)
    p.add_argument("public_harness", type=Path)
    p.add_argument("native_exit", type=int)
    args = p.parse_args()
    try:
        summary, valid = classify(
            args.owner_private_log.read_text(encoding="utf-8", errors="replace"),
            args.public_harness.read_text(encoding="utf-8"),
            args.native_exit)
    except (OSError, ValueError):
        print("V296_FRONTIER_AUDIT verified=0", file=sys.stderr)
        return 1
    print(summary)
    print(f"V296_FRONTIER_AUDIT verified={int(valid)}")
    return 0 if valid else 1

if __name__ == "__main__":
    sys.exit(main())
