#!/usr/bin/env python3
"""Derive V95 runner from V94."""
import argparse
from pathlib import Path
from derive_v94_es_open_runner import derive as previous

EDITS = [
  [
    "V94_SOURCE_ROOT",
    "V95_SOURCE_ROOT"
  ],
  [
    "run_v94_continuous_es_open.sh",
    "run_v95_continuous_title_return.sh"
  ],
  [
    "derive_v94_es_open_harness.py",
    "derive_v95_title_return_harness.py"
  ],
  [
    "derive_v94_es_open_generator.py",
    "derive_v95_title_return_generator.py"
  ],
  [
    "echo 'V94_STAGE geometry_verified'",
    "python3 \"$here/restore_ioctlv_v95.py\" \"$work/private.dol\" \"$owner\" \"$work/vector-request.dol\" > \"$work/extend-vector.log\" 2>&1 || {\n    echo 'V95 original vector fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/vector-request.dol\" \"$work/private.dol\"\necho 'V94_STAGE geometry_verified'"
  ],
  [
    "V94 recovered continuous original __start->ES open and title query assertions; mode=owner trials=16 stop=0x8051a62c",
    "V95 recovered continuous original __start->ES title query return assertions; mode=owner trials=16 stop=0x804f0ad8"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051A62C stage=94'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x804F0AD8 stage=95'"
  ],
  [
    "PASS: original Wii continuous __start completed fourth IOS open and reached original title query",
    "PASS: original Wii continuous __start completed genuine IOS title query and returned to NANDInit"
  ],
  [
    "  echo 'V94 original ES open and query continuation failed; details withheld' >&2",
    "  grep -E '^V95_VECTOR_SUBMIT flush=[01] wire=[01]$|^V95_TITLE_ACK wire=[01] output=[01]$|^V95_TITLE_RETURN route=[01] output=[01] abi=[01] prior=[01] vector=[01]$|^V95_DEPENDENCY pc=80[45][0-9a-f]{5} lr=80[45][0-9a-f]{5}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V95 original title query return failed; details withheld' >&2"
  ],
  [
    "echo 'V94_STAGE native_test_passed'",
    "echo 'V95_STAGE native_test_passed'\ngrep -E '^V95_VECTOR_SUBMIT flush=[01] wire=[01]$|^V95_TITLE_ACK wire=[01] output=[01]$|^V95_TITLE_RETURN route=[01] output=[01] abi=[01] prior=[01] vector=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V94_STAGE", "V95_STAGE").replace("V94_TRIAL_PASS", "V95_TRIAL_PASS")

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
