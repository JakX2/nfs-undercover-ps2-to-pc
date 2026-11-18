#!/usr/bin/env python3
"""Derive V103 runner from V102."""
import argparse
from pathlib import Path
from derive_v102_sc_path_runner import derive as previous

EDITS = [
  [
    "V102_SOURCE_ROOT",
    "V103_SOURCE_ROOT"
  ],
  [
    "run_v102_continuous_sc_path.sh",
    "run_v103_continuous_sc_async_entry.sh"
  ],
  [
    "derive_v102_sc_path_harness.py",
    "derive_v103_sc_async_entry_harness.py"
  ],
  [
    "derive_v102_sc_path_generator.py",
    "derive_v103_sc_async_entry_generator.py"
  ],
  [
    "echo 'V102_STAGE geometry_verified'",
    "python3 \"$here/restore_sc_async_entry_v103.py\" \"$work/private.dol\" \"$owner\" \"$work/sc-async.dol\" > \"$work/extend-sc-async.log\" 2>&1 || {\n    echo 'V103 original SC asynchronous wrapper fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/sc-async.dol\" \"$work/private.dol\"\necho 'V102_STAGE geometry_verified'"
  ],
  [
    "V102 recovered continuous original __start->SC pathname copy return assertions; mode=owner trials=16 stop=0x804f1e2c",
    "V103 recovered continuous original __start->IOS_OpenAsync entry assertions; mode=owner trials=16 stop=0x8051982c"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x804F1E2C stage=102'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051982C stage=103'"
  ],
  [
    "PASS: original Wii continuous __start executed SC pathname preparation to asynchronous open",
    "PASS: original Wii continuous __start executed SC asynchronous wrapper into IOS_OpenAsync"
  ],
  [
    "  echo 'V102 original SC pathname execution failed; details withheld' >&2",
    "  grep -E '^V103_SC_SAVE route=[01]$|^V103_SC_COPY bounded=[01] prior=[01]$|^V103_SC_ASYNC_ENTRY route=[01] path=[01] mode=[01] callback=[01] copied=[01] prior=[01] abi=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V103 original SC async open entry failed; details withheld' >&2"
  ],
  [
    "echo 'V102_STAGE native_test_passed'",
    "echo 'V103_STAGE native_test_passed'\ngrep -E '^V103_SC_SAVE route=[01]$|^V103_SC_COPY bounded=[01] prior=[01]$|^V103_SC_ASYNC_ENTRY route=[01] path=[01] mode=[01] callback=[01] copied=[01] prior=[01] abi=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V102_STAGE", "V103_STAGE").replace("V102_TRIAL_PASS", "V103_TRIAL_PASS")

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
