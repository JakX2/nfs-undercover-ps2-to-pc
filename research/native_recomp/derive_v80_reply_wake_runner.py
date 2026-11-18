#!/usr/bin/env python3
"""Derive a private V80 runner from the existing V79 source-only runner."""
import argparse
from pathlib import Path

EDITS = [
  [
    "here=\"$(cd \"$(dirname \"$0\")\" && pwd)\"",
    "here=\"${V80_SOURCE_ROOT:?V80 source root not set}\""
  ],
  [
    "run_v79_continuous_reply_entry.sh",
    "run_v80_continuous_reply_wake.sh"
  ],
  [
    "derive_v79_reply_harness.py",
    "derive_v80_reply_wake_harness.py"
  ],
  [
    "V79 recovered continuous original __start->reply processor entry assertions; mode=owner trials=16 stop=0x805190c0",
    "V80 recovered continuous original __start->reply wake entry assertions; mode=owner trials=16 stop=0x8052a51c"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x805190C0 stage=79",
    "BOOT_PROGRESS entry=0x8000403C pc=0x8052A51C stage=80"
  ],
  [
    "PASS: original Wii continuous __start entered original IOS reply processor after native context return",
    "PASS: original Wii continuous __start reached original waiting-thread wake entry"
  ],
  [
    "  echo 'V79 original reply entry assertion failed; details withheld' >&2",
    "  grep -E '^V80_WAKE_ENTRY route=[01] waiting=[01] wire=[01] consumed=[01]$|^V80_TRIAL_PASS trial=[0-9]{1,2}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V80 original wake entry assertion failed; details withheld' >&2"
  ],
  [
    "echo 'V79_STAGE native_test_passed'",
    "echo 'V80_STAGE native_test_passed'\ngrep -E '^V80_WAKE_ENTRY route=[01] waiting=[01] wire=[01] consumed=[01]$|^V80_TRIAL_PASS trial=[0-9]{1,2}$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V80 runner anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V79_STAGE", "V80_STAGE").replace("V79_TRIAL_PASS", "V80_TRIAL_PASS")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    result=derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x",encoding="utf-8") as f:
        f.write(result)

if __name__=="__main__":
    main()
