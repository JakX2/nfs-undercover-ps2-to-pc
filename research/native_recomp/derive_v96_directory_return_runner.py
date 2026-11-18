#!/usr/bin/env python3
"""Derive V96 runner from V95."""
import argparse
from pathlib import Path
from derive_v95_title_return_runner import derive as previous

EDITS = [
  [
    "V95_SOURCE_ROOT",
    "V96_SOURCE_ROOT"
  ],
  [
    "run_v95_continuous_title_return.sh",
    "run_v96_continuous_directory_return.sh"
  ],
  [
    "derive_v95_title_return_harness.py",
    "derive_v96_directory_return_harness.py"
  ],
  [
    "derive_v95_title_return_generator.py",
    "derive_v96_directory_return_generator.py"
  ],
  [
    "echo 'V95_STAGE geometry_verified'",
    "python3 \"$here/restore_directory_v96.py\" \"$work/private.dol\" \"$owner\" \"$work/dir-query.dol\" > \"$work/extend-dir-query.log\" 2>&1 || {\n    echo 'V96 original directory fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/dir-query.dol\" \"$work/private.dol\"\necho 'V95_STAGE geometry_verified'"
  ],
  [
    "V95 recovered continuous original __start->ES title query return assertions; mode=owner trials=16 stop=0x804f0ad8",
    "V96 recovered continuous original __start->ES directory query return assertions; mode=owner trials=16 stop=0x8054b4b4"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x804F0AD8 stage=95'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8054B4B4 stage=96'"
  ],
  [
    "PASS: original Wii continuous __start completed genuine IOS title query and returned to NANDInit",
    "PASS: original Wii continuous __start completed both ES metadata queries and returned to NANDInit"
  ],
  [
    "  echo 'V95 original title query return failed; details withheld' >&2",
    "  grep -E '^V96_DIRECTORY_REQUEST api=[01] vector=[01] title=[01]$|^V96_VECTOR_SUBMIT flush=[01] wire=[01]$|^V96_DIRECTORY_ACK wire=[01] output=[01]$|^V96_DIRECTORY_RETURN route=[01] data=[01] vector=[01] abi=[01] prior=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V96 original directory query return failed; details withheld' >&2"
  ],
  [
    "echo 'V95_STAGE native_test_passed'",
    "echo 'V96_STAGE native_test_passed'\ngrep -E '^V96_DIRECTORY_REQUEST api=[01] vector=[01] title=[01]$|^V96_VECTOR_SUBMIT flush=[01] wire=[01]$|^V96_DIRECTORY_ACK wire=[01] output=[01]$|^V96_DIRECTORY_RETURN route=[01] data=[01] vector=[01] abi=[01] prior=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V95_STAGE", "V96_STAGE").replace("V95_TRIAL_PASS", "V96_TRIAL_PASS")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    result = derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x", encoding="utf-8") as f:
        f.write(result)

if __name__ == "__main__":
    main()
