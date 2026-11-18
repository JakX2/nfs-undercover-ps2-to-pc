#!/usr/bin/env python3
"""Derive V101 runner from V100."""
import argparse
from pathlib import Path
from derive_v100_sc_status_runner import derive as previous

EDITS = [
  [
    "V100_SOURCE_ROOT",
    "V101_SOURCE_ROOT"
  ],
  [
    "run_v100_continuous_sc_status.sh",
    "run_v101_continuous_sc_loading.sh"
  ],
  [
    "derive_v100_sc_status_harness.py",
    "derive_v101_sc_loading_harness.py"
  ],
  [
    "derive_v100_sc_status_generator.py",
    "derive_v101_sc_loading_generator.py"
  ],
  [
    "echo 'V100_STAGE geometry_verified'",
    "python3 \"$here/restore_sc_loading_v101.py\" \"$work/private.dol\" \"$owner\" \"$work/sc-loading.dol\" > \"$work/extend-sc-loading.log\" 2>&1 || {\n    echo 'V101 original SC loading fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/sc-loading.dol\" \"$work/private.dol\"\necho 'V100_STAGE geometry_verified'"
  ],
  [
    "V100 recovered continuous original __start->SC status routing assertions; mode=owner trials=16 stop=0x8051dd50",
    "V101 recovered continuous original __start->SC configuration child entry assertions; mode=owner trials=16 stop=0x8051e71c"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051DD50 stage=100'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051E71C stage=101'"
  ],
  [
    "PASS: original Wii continuous __start entered SC status getter and selected original callback branch",
    "PASS: original Wii continuous __start ran SC configuration body into the original selected child"
  ],
  [
    "  echo 'V100 original SC status route failed; details withheld' >&2",
    "  grep -E '^V101_SC_SAVE route=[01]$|^V101_SC_CHILD route=[01] running=[01] prior=[01] kind=[12] arg=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V101 original SC loading child entry failed; details withheld' >&2"
  ],
  [
    "echo 'V100_STAGE native_test_passed'",
    "echo 'V101_STAGE native_test_passed'\ngrep -E '^V101_SC_SAVE route=[01]$|^V101_SC_CHILD route=[01] running=[01] prior=[01] kind=[12] arg=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V100_STAGE", "V101_STAGE").replace("V100_TRIAL_PASS", "V101_TRIAL_PASS")

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
