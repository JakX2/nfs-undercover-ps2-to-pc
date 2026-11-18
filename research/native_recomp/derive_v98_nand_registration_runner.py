#!/usr/bin/env python3
"""Derive V98 runner from V97."""
import argparse
from pathlib import Path
from derive_v97_es_close_runner import derive as previous

EDITS = [
  [
    "V97_SOURCE_ROOT",
    "V98_SOURCE_ROOT"
  ],
  [
    "run_v97_continuous_es_close.sh",
    "run_v98_continuous_nand_registration.sh"
  ],
  [
    "derive_v97_es_close_harness.py",
    "derive_v98_nand_registration_harness.py"
  ],
  [
    "V97 recovered continuous original __start->ES close return assertions; mode=owner trials=16 stop=0x80527b4c",
    "V98 recovered continuous original __start->NAND callback registration assertions; mode=owner trials=16 stop=0x8052f94c"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80527B4C stage=97'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8052F94C stage=98'"
  ],
  [
    "PASS: original Wii continuous __start completed original ES close and returned to NANDInit",
    "PASS: original Wii continuous __start registered NAND shutdown callback and returned from NANDInit to next original subsystem"
  ],
  [
    "  echo 'V97 original ES close return failed; details withheld' >&2",
    "  grep -E '^V98_NAND_SEQUENCE disable=[0-2] restore=[0-2] version=[0-1] report=[0-1] committed=[01]$|^V98_NAND_RETURN route=[01] stack=[01] status=[01]$|^V98_CONDITIONAL_HELPER selected=1$|^V98_NAND_CALLBACK route=[01] abi=[01] list=[01] directory=[01] state=[01] prior=[01]$|^V98_VERSION_POINTER nonzero=[01] owner=[01]$|^V98_INITIAL_DATA count=[0-9]{1,2}$|^V98_DEPENDENCY pc=80[45][0-9a-f]{5} lr=80[45][0-9a-f]{5}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V98 original NAND registration failed; details withheld' >&2"
  ],
  [
    "echo 'V97_STAGE native_test_passed'",
    "echo 'V98_STAGE native_test_passed'\ngrep -E '^V98_NAND_SEQUENCE disable=[0-2] restore=[0-2] version=[0-1] report=[0-1] committed=[01]$|^V98_NAND_RETURN route=[01] stack=[01] status=[01]$|^V98_CONDITIONAL_HELPER selected=1$|^V98_NAND_CALLBACK route=[01] abi=[01] list=[01] directory=[01] state=[01] prior=[01]$|^V98_VERSION_POINTER nonzero=[01] owner=[01]$|^V98_INITIAL_DATA count=[0-9]{1,2}$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V97_STAGE", "V98_STAGE").replace("V97_TRIAL_PASS", "V98_TRIAL_PASS")

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
