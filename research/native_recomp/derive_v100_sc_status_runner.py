#!/usr/bin/env python3
"""Derive V100 runner from V99."""
import argparse
from pathlib import Path
from derive_v99_post_nand_runner import derive as previous

EDITS = [
  [
    "V99_SOURCE_ROOT",
    "V100_SOURCE_ROOT"
  ],
  [
    "run_v99_continuous_post_nand.sh",
    "run_v100_continuous_sc_status.sh"
  ],
  [
    "derive_v99_post_nand_harness.py",
    "derive_v100_sc_status_harness.py"
  ],
  [
    "derive_v99_post_nand_generator.py",
    "derive_v100_sc_status_generator.py"
  ],
  [
    "echo 'V99_STAGE geometry_verified'",
    "python3 \"$here/restore_sc_status_v100.py\" \"$work/private.dol\" \"$owner\" \"$work/sc-status.dol\" > \"$work/extend-sc-status.log\" 2>&1 || {\n    echo 'V100 original SC status fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/sc-status.dol\" \"$work/private.dol\"\necho 'V99_STAGE geometry_verified'"
  ],
  [
    "V99 recovered continuous original __start->post NAND memory helper assertions; mode=owner trials=16 stop=0x8051dff4",
    "V100 recovered continuous original __start->SC status routing assertions; mode=owner trials=16 stop=0x8051dd50"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051DFF4 stage=99'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051DD50 stage=100'"
  ],
  [
    "PASS: original Wii continuous __start completed post NAND original memory preparation",
    "PASS: original Wii continuous __start entered SC status getter and selected original callback branch"
  ],
  [
    "  echo 'V99 original post NAND sibling failed; details withheld' >&2",
    "  grep -E '^V100_SC_ENTRY status=[01]$|^V100_SC_STATUS entry=[01]$|^V100_SC_ROUTE route=[01] thread=[01] prior=[01] chosen=[12]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V100 original SC status route failed; details withheld' >&2"
  ],
  [
    "echo 'V99_STAGE native_test_passed'",
    "echo 'V100_STAGE native_test_passed'\ngrep -E '^V100_SC_ENTRY status=[01]$|^V100_SC_STATUS entry=[01]$|^V100_SC_ROUTE route=[01] thread=[01] prior=[01] chosen=[12]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V99_STAGE", "V100_STAGE").replace("V99_TRIAL_PASS", "V100_TRIAL_PASS")

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
