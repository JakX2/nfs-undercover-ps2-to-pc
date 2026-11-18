#!/usr/bin/env python3
"""Derive V94 runner from V93."""
import argparse
from pathlib import Path
from derive_v93_isfs_return_runner import derive as previous

EDITS = [
  [
    "V93_SOURCE_ROOT",
    "V94_SOURCE_ROOT"
  ],
  [
    "run_v93_continuous_isfs_return.sh",
    "run_v94_continuous_es_open.sh"
  ],
  [
    "derive_v93_isfs_return_harness.py",
    "derive_v94_es_open_harness.py"
  ],
  [
    "derive_v93_isfs_return_generator.py",
    "derive_v94_es_open_generator.py"
  ],
  [
    "echo 'V93_STAGE geometry_verified'",
    "python3 \"$here/restore_title_query_v94.py\" \"$work/private.dol\" \"$owner\" \"$work/title-query.dol\" > \"$work/extend-title-query.log\" 2>&1 || {\n    echo 'V94 original title query fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/title-query.dol\" \"$work/private.dol\"\necho 'V93_STAGE geometry_verified'"
  ],
  [
    "V93 recovered continuous original __start->filesystem init and next service open assertions; mode=owner trials=16 stop=0x80519944",
    "V94 recovered continuous original __start->ES open and title query assertions; mode=owner trials=16 stop=0x8051a62c"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80519944 stage=93'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051A62C stage=94'"
  ],
  [
    "PASS: original Wii continuous __start completed filesystem initialization and reached ES open",
    "PASS: original Wii continuous __start completed fourth IOS open and reached original title query"
  ],
  [
    "  echo 'V93 original filesystem initialization continuation failed; details withheld' >&2",
    "  grep -E '^V94_ES_ACK prior=[01] event=[01]$|^V94_ES_RETURN route=[01] result=[01] prior=[01] deferred=[01] abi=[01]$|^V94_TITLE_REQUEST route=[01] api=[01] vector=[01] prior=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V94 original ES open and query continuation failed; details withheld' >&2"
  ],
  [
    "echo 'V93_STAGE native_test_passed'",
    "echo 'V94_STAGE native_test_passed'\ngrep -E '^V94_ES_ACK prior=[01] event=[01]$|^V94_ES_RETURN route=[01] result=[01] prior=[01] deferred=[01] abi=[01]$|^V94_TITLE_REQUEST route=[01] api=[01] vector=[01] prior=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V93_STAGE", "V94_STAGE").replace("V93_TRIAL_PASS", "V94_TRIAL_PASS")

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
