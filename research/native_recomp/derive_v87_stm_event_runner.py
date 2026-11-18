#!/usr/bin/env python3
"""Derive V87 runner from V86."""
import argparse
from pathlib import Path
from derive_v86_stm_ioctl_runner import derive as previous

EDITS = [
  [
    "V86_SOURCE_ROOT",
    "V87_SOURCE_ROOT"
  ],
  [
    "run_v86_continuous_stm_ioctl.sh",
    "run_v87_continuous_stm_event.sh"
  ],
  [
    "derive_v86_stm_ioctl_harness.py",
    "derive_v87_stm_event_harness.py"
  ],
  [
    "V86 recovered continuous original __start->asynchronous STM submission entry assertions; mode=owner trials=16 stop=0x805195ec",
    "V87 recovered continuous original __start->asynchronous STM event registration assertions; mode=owner trials=16 stop=0x805265d4"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=86",
    "BOOT_PROGRESS entry=0x8000403C pc=0x805265D4 stage=87"
  ],
  [
    "PASS: original Wii continuous __start reached genuine async STM submission",
    "PASS: original Wii continuous __start registered deferred native STM event"
  ],
  [
    "  echo 'V86 original STM async submission failed; details withheld' >&2",
    "  grep -E '^V87_ASYNC_RETURN route=[01] descriptors=[01] thread=[01] sent=[01] before=[01]$|^V87_DEFERRED pending=[01] ack=[01] wire=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V87 original STM event registration failed; details withheld' >&2"
  ],
  [
    "echo 'V86_STAGE native_test_passed'",
    "echo 'V87_STAGE native_test_passed'\ngrep -E '^V87_ASYNC_RETURN route=[01] descriptors=[01] thread=[01] sent=[01] before=[01]$|^V87_DEFERRED pending=[01] ack=[01] wire=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V86_STAGE", "V87_STAGE").replace("V86_TRIAL_PASS", "V87_TRIAL_PASS")

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
