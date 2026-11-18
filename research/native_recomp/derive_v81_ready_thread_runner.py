#!/usr/bin/env python3
"""Derive V81 runner from V80."""
import argparse
from pathlib import Path
from derive_v80_reply_wake_runner import derive as previous

EDITS = [
  [
    "V80_SOURCE_ROOT",
    "V81_SOURCE_ROOT"
  ],
  [
    "run_v80_continuous_reply_wake.sh",
    "run_v81_continuous_ready_thread.sh"
  ],
  [
    "derive_v80_reply_wake_harness.py",
    "derive_v81_ready_thread_harness.py"
  ],
  [
    "V80 recovered continuous original __start->reply wake entry assertions; mode=owner trials=16 stop=0x8052a51c",
    "V81 recovered continuous original __start->ready thread scheduler entry assertions; mode=owner trials=16 stop=0x80529718"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x8052A51C stage=80",
    "BOOT_PROGRESS entry=0x8000403C pc=0x80529718 stage=81"
  ],
  [
    "PASS: original Wii continuous __start reached original waiting-thread wake entry",
    "PASS: original Wii continuous __start woke and enqueued original waiting thread"
  ],
  [
    "  echo 'V80 original wake entry assertion failed; details withheld' >&2",
    "  grep -E '^V81_READY_STATE route=[01] drained=[01] ready=[01] enrolled=[01] idle=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V81 original ready thread assertion failed; details withheld' >&2"
  ],
  [
    "echo 'V80_STAGE native_test_passed'",
    "echo 'V81_STAGE native_test_passed'\ngrep -E '^V81_READY_STATE route=[01] drained=[01] ready=[01] enrolled=[01] idle=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V81 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V80_STAGE", "V81_STAGE").replace("V80_TRIAL_PASS", "V81_TRIAL_PASS")

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
