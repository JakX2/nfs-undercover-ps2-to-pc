#!/usr/bin/env python3
"""Privacy-safe V39 native assertion classification from public harness literals.

Report only a numeric assertion ID; the owner-original native log stays in
private runner scratch and is never uploaded.
"""
from __future__ import annotations
import argparse
from pathlib import Path

from classify_v38_native_failure import classify

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("native_private_log",type=Path)
    p.add_argument("public_test_cpp",type=Path)
    a=p.parse_args()
    code=classify(a.public_test_cpp.read_text(encoding="utf-8"),
                  a.native_private_log.read_text(encoding="utf-8",errors="replace"))
    print(f"V39_NATIVE_ASSERTION id={code:03d}")

if __name__=="__main__":
    main()
