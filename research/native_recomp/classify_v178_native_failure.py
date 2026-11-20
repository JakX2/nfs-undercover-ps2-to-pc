#!/usr/bin/env python3
"""V178 bounded numeric IDs for public assertions in large native harnesses.

The legacy V38 classifier only emits three-digit IDs. The continuously
derived Wii startup harness now has more source-owned diagnostic strings,
and a late assertion index can exceed 999. Resolve exact matches against
*public harness strings* without printing the private owner log or the
matching message. V178 uses four decimal digits and fails closed on overflow.
No game code or private bytes are read except the owner's ephemeral log.
"""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING, ERROR

MAX_LABELS = 9999

def classify_public(source: str, private_log: str) -> int:
    messages=sorted(set(STRING.findall(source)))
    for candidate in ERROR.findall(private_log):
        try:
            index=messages.index(candidate)+1
        except ValueError:
            continue
        if index>MAX_LABELS:
            raise ValueError("V178 source-only assertion catalog exceeds bound")
        return index
    return 0

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("public_native_test",type=Path)
    a=p.parse_args()
    index=classify_public(
        a.public_native_test.read_text(encoding="utf-8"),
        a.private_native_log.read_text(encoding="utf-8",errors="replace"))
    print(f"V178_NATIVE_ASSERTION id={index:04d}")

if __name__=="__main__":
    main()
