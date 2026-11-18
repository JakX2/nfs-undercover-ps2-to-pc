#!/usr/bin/env python3
"""Derive V88 runner from V87."""
import argparse
from pathlib import Path
from derive_v87_stm_event_runner import derive as previous

EDITS = [
  [
    "V87_SOURCE_ROOT",
    "V88_SOURCE_ROOT"
  ],
  [
    "run_v87_continuous_stm_event.sh",
    "run_v88_continuous_stm_return.sh"
  ],
  [
    "derive_v87_stm_event_harness.py",
    "derive_v88_stm_return_harness.py"
  ],
  [
    "V87 recovered continuous original __start->asynchronous STM event registration assertions; mode=owner trials=16 stop=0x805265d4",
    "V88 recovered continuous original __start->STM return after deferred ACK assertions; mode=owner trials=16 stop=0x80520968"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x805265D4 stage=87",
    "BOOT_PROGRESS entry=0x8000403C pc=0x80520968 stage=88"
  ],
  [
    "PASS: original Wii continuous __start registered deferred native STM event",
    "PASS: original Wii continuous __start returned from original STM initialization"
  ],
  [
    "  echo 'V87 original STM event registration failed; details withheld' >&2",
    "  grep -E '^V88_ACTIVE_VECTOR route=[01] saved=[01] running=[01] masked=[01]$|^V88_ACTIVE_ACK clear=[01] deferred=[01] running=[01] route=[01]$|^V88_ACTIVE_RFI regs=[01] status=[01] running=[01] deferred=[01]$|^V88_STM_RETURN route=[01] abi=[01] running=[01] deferred=[01] devices=[01]$|^V88_DEPENDENCY pc=80[45][0-9a-f]{5} lr=80[45][0-9a-f]{5}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V88 original STM return failed; details withheld' >&2"
  ],
  [
    "echo 'V87_STAGE native_test_passed'",
    "echo 'V88_STAGE native_test_passed'\ngrep -E '^V88_ACTIVE_VECTOR route=[01] saved=[01] running=[01] masked=[01]$|^V88_ACTIVE_ACK clear=[01] deferred=[01] running=[01] route=[01]$|^V88_ACTIVE_RFI regs=[01] status=[01] running=[01] deferred=[01]$|^V88_STM_RETURN route=[01] abi=[01] running=[01] deferred=[01] devices=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V87_STAGE", "V88_STAGE").replace("V87_TRIAL_PASS", "V88_TRIAL_PASS")

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
