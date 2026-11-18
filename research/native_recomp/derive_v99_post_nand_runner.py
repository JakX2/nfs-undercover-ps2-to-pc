#!/usr/bin/env python3
"""Derive V99 runner from V98."""
import argparse
from pathlib import Path
from derive_v98_nand_registration_runner import derive as previous

EDITS = [
  [
    "V98_SOURCE_ROOT",
    "V99_SOURCE_ROOT"
  ],
  [
    "run_v98_continuous_nand_registration.sh",
    "run_v99_continuous_post_nand.sh"
  ],
  [
    "derive_v98_nand_registration_harness.py",
    "derive_v99_post_nand_harness.py"
  ],
  [
    "derive_v97_es_close_generator.py",
    "derive_v99_post_nand_generator.py"
  ],
  [
    "echo 'V98_STAGE geometry_verified'",
    "python3 \"$here/restore_post_nand_v99.py\" \"$work/private.dol\" \"$owner\" \"$work/post-nand.dol\" > \"$work/extend-post-nand.log\" 2>&1 || {\n    echo 'V99 original post NAND fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/post-nand.dol\" \"$work/private.dol\"\necho 'V98_STAGE geometry_verified'"
  ],
  [
    "V98 recovered continuous original __start->NAND callback registration assertions; mode=owner trials=16 stop=0x8052f94c",
    "V99 recovered continuous original __start->post NAND memory helper assertions; mode=owner trials=16 stop=0x8051dff4"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8052F94C stage=98'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051DFF4 stage=99'"
  ],
  [
    "PASS: original Wii continuous __start registered NAND shutdown callback and returned from NANDInit to next original subsystem",
    "PASS: original Wii continuous __start completed post NAND original memory preparation"
  ],
  [
    "  echo 'V98 original NAND registration failed; details withheld' >&2",
    "  grep -E '^V99_SIBLING_MEMORY route=[01] abi=[01] data=[01] prior=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V99 original post NAND sibling failed; details withheld' >&2"
  ],
  [
    "echo 'V98_STAGE native_test_passed'",
    "echo 'V99_STAGE native_test_passed'\ngrep -E '^V99_SIBLING_MEMORY route=[01] abi=[01] data=[01] prior=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V98_STAGE", "V99_STAGE").replace("V98_TRIAL_PASS", "V99_TRIAL_PASS")

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
