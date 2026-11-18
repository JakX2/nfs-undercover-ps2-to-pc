#!/usr/bin/env python3
"""Derive V92 runner from V91."""
import argparse
from pathlib import Path
from derive_v91_resource_open_runner import derive as previous

EDITS = [
  [
    "V91_SOURCE_ROOT",
    "V92_SOURCE_ROOT"
  ],
  [
    "run_v91_continuous_resource_open.sh",
    "run_v92_continuous_filesystem_return.sh"
  ],
  [
    "derive_v91_resource_open_harness.py",
    "derive_v92_filesystem_return_harness.py"
  ],
  [
    "V91 recovered continuous original __start->next IOS resource open assertions; mode=owner trials=16 stop=0x80519944",
    "V92 recovered continuous original __start->filesystem open return assertions; mode=owner trials=16 stop=0x8051908c"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80519944 stage=91'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051908C stage=92'"
  ],
  [
    "PASS: original Wii continuous __start reached next original IOS resource open",
    "PASS: original Wii continuous __start completed real filesystem open and original return"
  ],
  [
    "  echo 'V91 original resource initialization failed; details withheld' >&2",
    "  grep -E '^V92_FS_ACK prior=[01] event=[01]$|^V92_FS_RETURN route=[01] result=[01] descriptors=[01] deferred=[01] abi=[01] idle=[01] bounds=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V92 original filesystem open return failed; details withheld' >&2"
  ],
  [
    "echo 'V91_STAGE native_test_passed'",
    "echo 'V92_STAGE native_test_passed'\ngrep -E '^V92_FS_ACK prior=[01] event=[01]$|^V92_FS_RETURN route=[01] result=[01] descriptors=[01] deferred=[01] abi=[01] idle=[01] bounds=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V91_STAGE", "V92_STAGE").replace("V91_TRIAL_PASS", "V92_TRIAL_PASS")

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
