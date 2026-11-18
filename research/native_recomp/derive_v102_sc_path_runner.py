#!/usr/bin/env python3
"""Derive V102 runner from V101."""
import argparse
from pathlib import Path
from derive_v101_sc_loading_runner import derive as previous

EDITS = [
  [
    "V101_SOURCE_ROOT",
    "V102_SOURCE_ROOT"
  ],
  [
    "run_v101_continuous_sc_loading.sh",
    "run_v102_continuous_sc_path.sh"
  ],
  [
    "derive_v101_sc_loading_harness.py",
    "derive_v102_sc_path_harness.py"
  ],
  [
    "derive_v101_sc_loading_generator.py",
    "derive_v102_sc_path_generator.py"
  ],
  [
    "echo 'V101_STAGE geometry_verified'",
    "python3 \"$here/restore_sc_path_v102.py\" \"$work/private.dol\" \"$owner\" \"$work/sc-path.dol\" > \"$work/extend-sc-path.log\" 2>&1 || {\n    echo 'V102 original SC pathname fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/sc-path.dol\" \"$work/private.dol\"\necho 'V101_STAGE geometry_verified'"
  ],
  [
    "V101 recovered continuous original __start->SC configuration child entry assertions; mode=owner trials=16 stop=0x8051e71c",
    "V102 recovered continuous original __start->SC pathname copy return assertions; mode=owner trials=16 stop=0x804f1e2c"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051E71C stage=101'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x804F1E2C stage=102'"
  ],
  [
    "PASS: original Wii continuous __start ran SC configuration body into the original selected child",
    "PASS: original Wii continuous __start executed SC pathname preparation to asynchronous open"
  ],
  [
    "  echo 'V101 original SC loading child entry failed; details withheld' >&2",
    "  grep -E '^V102_SC_STRLEN input=[01] bounded=[01]$|^V102_SC_COPY input=[01] bounded=[01]$|^V102_SC_PATH route=[01] bytes=[01] abi=[01] prior=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V102 original SC pathname execution failed; details withheld' >&2"
  ],
  [
    "echo 'V101_STAGE native_test_passed'",
    "echo 'V102_STAGE native_test_passed'\ngrep -E '^V102_SC_STRLEN input=[01] bounded=[01]$|^V102_SC_COPY input=[01] bounded=[01]$|^V102_SC_PATH route=[01] bytes=[01] abi=[01] prior=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V101_STAGE", "V102_STAGE").replace("V101_TRIAL_PASS", "V102_TRIAL_PASS")

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
