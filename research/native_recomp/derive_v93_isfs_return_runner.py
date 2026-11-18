#!/usr/bin/env python3
"""Derive V93 runner from V92."""
import argparse
from pathlib import Path
from derive_v92_filesystem_return_runner import derive as previous

EDITS = [
  [
    "V92_SOURCE_ROOT",
    "V93_SOURCE_ROOT"
  ],
  [
    "run_v92_continuous_filesystem_return.sh",
    "run_v93_continuous_isfs_return.sh"
  ],
  [
    "derive_v92_filesystem_return_harness.py",
    "derive_v93_isfs_return_harness.py"
  ],
  [
    "derive_v91_resource_open_generator.py",
    "derive_v93_isfs_return_generator.py"
  ],
  [
    "echo 'V92_STAGE geometry_verified'",
    "python3 \"$here/restore_next_resource_v93.py\" \"$work/private.dol\" \"$owner\" \"$work/next-resource.dol\" > \"$work/extend-next-resource.log\" 2>&1 || {\n    echo 'V93 original next resource fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/next-resource.dol\" \"$work/private.dol\"\necho 'V92_STAGE geometry_verified'"
  ],
  [
    "V92 recovered continuous original __start->filesystem open return assertions; mode=owner trials=16 stop=0x8051908c",
    "V93 recovered continuous original __start->filesystem init and next service open assertions; mode=owner trials=16 stop=0x80519944"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051908C stage=92'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80519944 stage=93'"
  ],
  [
    "PASS: original Wii continuous __start completed real filesystem open and original return",
    "PASS: original Wii continuous __start completed filesystem initialization and reached ES open"
  ],
  [
    "  echo 'V92 original filesystem open return failed; details withheld' >&2",
    "  grep -E '^V93_HEAP_ENTRY route=[01] bounds=[01]$|^V93_ISFS_RETURN route=[01] result=[01] memory=[01] state=[01] preserved=[01]$|^V93_NEXT_OPEN route=[01] service=[01] preserved=[01]$|^V93_DEPENDENCY pc=80[45][0-9a-f]{5} lr=80[45][0-9a-f]{5}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V93 original filesystem initialization continuation failed; details withheld' >&2"
  ],
  [
    "echo 'V92_STAGE native_test_passed'",
    "echo 'V93_STAGE native_test_passed'\ngrep -E '^V93_HEAP_ENTRY route=[01] bounds=[01]$|^V93_ISFS_RETURN route=[01] result=[01] memory=[01] state=[01] preserved=[01]$|^V93_NEXT_OPEN route=[01] service=[01] preserved=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V92_STAGE", "V93_STAGE").replace("V92_TRIAL_PASS", "V93_TRIAL_PASS")

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
