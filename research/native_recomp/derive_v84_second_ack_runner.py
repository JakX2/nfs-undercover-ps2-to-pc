#!/usr/bin/env python3
"""Derive V84 runner from V83."""
import argparse
from pathlib import Path
from derive_v83_second_open_runner import derive as previous

EDITS = [
  [
    "V83_SOURCE_ROOT",
    "V84_SOURCE_ROOT"
  ],
  [
    "run_v83_continuous_second_open.sh",
    "run_v84_continuous_second_ack.sh"
  ],
  [
    "derive_v83_second_open_harness.py",
    "derive_v84_second_ack_harness.py"
  ],
  [
    "V83 recovered continuous original __start->second STM open assertions; mode=owner trials=16 stop=0x80519944",
    "V84 recovered continuous original __start->second STM ACK assertions; mode=owner trials=16 stop=0x8052a430"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x80519944 stage=83",
    "BOOT_PROGRESS entry=0x8000403C pc=0x8052A430 stage=84"
  ],
  [
    "PASS: original Wii continuous __start returned from first IOS_Open to second STM open",
    "PASS: original Wii continuous __start acknowledged second original STM Open request"
  ],
  [
    "  echo 'V83 original second open assertion failed; details withheld' >&2",
    "  grep -E '^V84_SECOND_ACK first=[01] second=[01] wire=[01] pending=[01] route=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V84 original second ACK assertion failed; details withheld' >&2"
  ],
  [
    "echo 'V83_STAGE native_test_passed'",
    "echo 'V84_STAGE native_test_passed'\ngrep -E '^V84_SECOND_ACK first=[01] second=[01] wire=[01] pending=[01] route=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V83_STAGE", "V84_STAGE").replace("V83_TRIAL_PASS", "V84_TRIAL_PASS")

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
