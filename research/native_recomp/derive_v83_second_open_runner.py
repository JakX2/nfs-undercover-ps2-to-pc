#!/usr/bin/env python3
"""Derive V83 runner from V82."""
import argparse
from pathlib import Path
from derive_v82_thread_resume_runner import derive as previous

EDITS = [
  [
    "V82_SOURCE_ROOT",
    "V83_SOURCE_ROOT"
  ],
  [
    "run_v82_continuous_thread_resume.sh",
    "run_v83_continuous_second_open.sh"
  ],
  [
    "derive_v82_thread_resume_harness.py",
    "derive_v83_second_open_harness.py"
  ],
  [
    "V82 recovered continuous original __start->sleeping thread resumed assertions; mode=owner trials=16 stop=0x805265d4",
    "V83 recovered continuous original __start->second STM open assertions; mode=owner trials=16 stop=0x80519944"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x805265D4 stage=82",
    "BOOT_PROGRESS entry=0x8000403C pc=0x80519944 stage=83"
  ],
  [
    "PASS: original Wii continuous __start resumed original sleeping thread",
    "PASS: original Wii continuous __start returned from first IOS_Open to second STM open"
  ],
  [
    "  echo 'V82 original thread resume assertion failed; details withheld' >&2",
    "  grep -E '^V83_FREE_ENTRY request=[01] result=[01] route=[01]$|^V83_SECOND_OPEN first=[01] next=[01] abi=[01] cleanup=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V83 original second open assertion failed; details withheld' >&2"
  ],
  [
    "echo 'V82_STAGE native_test_passed'",
    "echo 'V83_STAGE native_test_passed'\ngrep -E '^V83_FREE_ENTRY request=[01] result=[01] route=[01]$|^V83_SECOND_OPEN first=[01] next=[01] abi=[01] cleanup=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V82_STAGE", "V83_STAGE").replace("V82_TRIAL_PASS", "V83_TRIAL_PASS")

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
