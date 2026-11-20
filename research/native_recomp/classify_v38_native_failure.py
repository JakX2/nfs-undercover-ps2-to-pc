#!/usr/bin/env python3
"""Classify a V38 native assertion using ORIGINAL-FREE public C++ strings.

Only a numeric ID derived from a fixed public test-harness string is emitted.
Never output the private log, exception text, code bytes, path or guest data.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')
ERROR = re.compile(r"what\(\):\s+([^\r\n]+)")


def classify(source: str, private_log: str) -> int:
    messages=sorted(set(STRING.findall(source)))
    for candidate in ERROR.findall(private_log):
        if candidate in messages:
            index=messages.index(candidate)+1
            # Four-digit IDs are needed for the growing original-free native
            # harness. Never derive labels from any private game material.
            if index>9999:
                raise ValueError("public assertion catalog exceeds 4-digit bound")
            return index
    return 0


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("native_private_log",type=Path)
    p.add_argument("public_test_cpp",type=Path)
    a=p.parse_args()
    # Only test-harness-owned diagnostics can be classified; private logs
    # are never printed or uploaded, even when unrecognized or malformed.
    code=classify(a.public_test_cpp.read_text(encoding="utf-8"),
                  a.native_private_log.read_text(encoding="utf-8",errors="replace"))
    print(f"V38_NATIVE_ASSERTION id={code:03d}")


if __name__=="__main__":
    main()
