#!/usr/bin/env python3
"""Derive V97 runner from V96."""
import argparse
from pathlib import Path
from derive_v96_directory_return_runner import derive as previous

EDITS = [
  [
    "V96_SOURCE_ROOT",
    "V97_SOURCE_ROOT"
  ],
  [
    "run_v96_continuous_directory_return.sh",
    "run_v97_continuous_es_close.sh"
  ],
  [
    "derive_v96_directory_return_harness.py",
    "derive_v97_es_close_harness.py"
  ],
  [
    "derive_v96_directory_return_generator.py",
    "derive_v97_es_close_generator.py"
  ],
  [
    "echo 'V96_STAGE geometry_verified'",
    "python3 \"$here/restore_es_close_v97.py\" \"$work/private.dol\" \"$owner\" \"$work/es-close.dol\" > \"$work/extend-es-close.log\" 2>&1 || {\n    echo 'V97 original close fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/es-close.dol\" \"$work/private.dol\"\necho 'V96_STAGE geometry_verified'"
  ],
  [
    "V96 recovered continuous original __start->ES directory query return assertions; mode=owner trials=16 stop=0x8054b4b4",
    "V97 recovered continuous original __start->ES close return assertions; mode=owner trials=16 stop=0x80527b4c"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8054B4B4 stage=96'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80527B4C stage=97'"
  ],
  [
    "PASS: original Wii continuous __start completed both ES metadata queries and returned to NANDInit",
    "PASS: original Wii continuous __start completed original ES close and returned to NANDInit"
  ],
  [
    "  echo 'V96 original directory query return failed; details withheld' >&2",
    "  grep -E '^V97_DIRECTORY_COPY copied=[01]$|^V97_CLOSE_ACK wire=[01] closed=[01]$|^V97_ES_RETURN route=[01] closed=[01] prior=[01] abi=[01] callback=[01]$|^V97_DEPENDENCY pc=80[45][0-9a-f]{5} lr=80[45][0-9a-f]{5}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V97 original ES close return failed; details withheld' >&2"
  ],
  [
    "echo 'V96_STAGE native_test_passed'",
    "echo 'V97_STAGE native_test_passed'\ngrep -E '^V97_DIRECTORY_COPY copied=[01]$|^V97_CLOSE_ACK wire=[01] closed=[01]$|^V97_ES_RETURN route=[01] closed=[01] prior=[01] abi=[01] callback=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V96_STAGE", "V97_STAGE").replace("V96_TRIAL_PASS", "V97_TRIAL_PASS")

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
