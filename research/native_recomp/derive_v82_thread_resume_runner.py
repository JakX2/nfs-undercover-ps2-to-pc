#!/usr/bin/env python3
"""Derive V82 runner from V81."""
import argparse
from pathlib import Path
from derive_v81_ready_thread_runner import derive as previous

EDITS = [
  [
    "V81_SOURCE_ROOT",
    "V82_SOURCE_ROOT"
  ],
  [
    "run_v81_continuous_ready_thread.sh",
    "run_v82_continuous_thread_resume.sh"
  ],
  [
    "derive_v81_ready_thread_harness.py",
    "derive_v82_thread_resume_harness.py"
  ],
  [
    "V81 recovered continuous original __start->ready thread scheduler entry assertions; mode=owner trials=16 stop=0x80529718",
    "V82 recovered continuous original __start->sleeping thread resumed assertions; mode=owner trials=16 stop=0x805265d4"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x80529718 stage=81",
    "BOOT_PROGRESS entry=0x8000403C pc=0x805265D4 stage=82"
  ],
  [
    "PASS: original Wii continuous __start woke and enqueued original waiting thread",
    "PASS: original Wii continuous __start resumed original sleeping thread"
  ],
  [
    "  echo 'V81 original ready thread assertion failed; details withheld' >&2",
    "  grep -E '^V82_REPLY_RETURN clear=[01] ready=[01] route=[01]$|^V82_LOAD_CONTEXT selected=[01] running=[01] saved=[01]$|^V82_RESUME_STATE running=[01] stack=[01] queue=[01] route=[01]$' \"$work/private-native.log\" | sort -u || true\n  grep -E '^V82_IDLE_LOAD route=[01] ready=[01] idle=[01] clear=[01]$|^V82_IDLE_RFI regs=[01] status=[01] ready=[01] clear=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V82 original thread resume assertion failed; details withheld' >&2"
  ],
  [
    "echo 'V81_STAGE native_test_passed'",
    "echo 'V82_STAGE native_test_passed'\ngrep -E '^V82_REPLY_RETURN clear=[01] ready=[01] route=[01]$|^V82_LOAD_CONTEXT selected=[01] running=[01] saved=[01]$|^V82_RESUME_STATE running=[01] stack=[01] queue=[01] route=[01]$' \"$work/private-native.log\" | sort -u\ngrep -E '^V82_IDLE_LOAD route=[01] ready=[01] idle=[01] clear=[01]$|^V82_IDLE_RFI regs=[01] status=[01] ready=[01] clear=[01]$' \"$work/private-native.log\" | sort -u || true"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V82 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V81_STAGE", "V82_STAGE").replace("V81_TRIAL_PASS", "V82_TRIAL_PASS")

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
