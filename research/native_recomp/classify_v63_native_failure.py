#!/usr/bin/env python3
"""V63 original-free numeric assertion IDs. Private logs never leave CI."""
from __future__ import annotations
import argparse
from pathlib import Path
from classify_v38_native_failure import classify

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("public_native_test",type=Path)
    a=p.parse_args()
    value=classify(a.public_native_test.read_text(encoding="utf-8"),
                   a.private_native_log.read_text(encoding="utf-8",errors="replace"))
    print(f"V63_NATIVE_ASSERTION id={value:03d}")
if __name__=="__main__":
    main()
