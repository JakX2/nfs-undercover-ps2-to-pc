#!/usr/bin/env python3
"""Derive V85 runner from V84."""
import argparse
from pathlib import Path
from derive_v84_second_ack_runner import derive as previous

EDITS = [
  [
    "V84_SOURCE_ROOT",
    "V85_SOURCE_ROOT"
  ],
  [
    "run_v84_continuous_second_ack.sh",
    "run_v85_continuous_both_stm_opens.sh"
  ],
  [
    "derive_v84_second_ack_harness.py",
    "derive_v85_both_stm_opens_harness.py"
  ],
  [
    "V84 recovered continuous original __start->second STM ACK assertions; mode=owner trials=16 stop=0x8052a430",
    "V85 recovered continuous original __start->both STM opens completed assertions; mode=owner trials=16 stop=0x805265ac"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x8052A430 stage=84",
    "BOOT_PROGRESS entry=0x8000403C pc=0x805265AC stage=85"
  ],
  [
    "PASS: original Wii continuous __start acknowledged second original STM Open request",
    "PASS: original Wii continuous __start returned from both original STM opens"
  ],
  [
    "  echo 'V84 original second ACK assertion failed; details withheld' >&2",
    "  grep -E '^V85_STM_OPENS descriptors=[01] idle=[01] cleanup=[01] abi=[01] route=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V85 original dual STM opens failed; details withheld' >&2"
  ],
  [
    "echo 'V84_STAGE native_test_passed'",
    "echo 'V85_STAGE native_test_passed'\ngrep -E '^V85_STM_OPENS descriptors=[01] idle=[01] cleanup=[01] abi=[01] route=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V84_STAGE", "V85_STAGE").replace("V84_TRIAL_PASS", "V85_TRIAL_PASS")

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
