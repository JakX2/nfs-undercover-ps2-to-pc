#!/usr/bin/env python3
"""V136 preserve V133 owner checks, then require a complete second SC retry."""
import argparse
from pathlib import Path
from derive_v133_sc_sda_runner import derive as previous

OLD = 'python3 "$here/derive_v133_sc_sda_harness.py"'
NEW = 'python3 "$here/derive_v136_second_retry_harness.py"'
FAIL = "  echo 'V130_NATIVE_EXIT ok=0'"
DONE = "echo 'V133_STATUS_PROBE verified=1'"

def derive(source: str) -> str:
    s = previous(source)
    if s.count(OLD) != 1 or s.count(FAIL) != 1 or s.count(DONE) != 1:
        raise ValueError("V136 inherited source-owned runner markers differ")
    s = s.replace(OLD, NEW, 1)
    # This output is a bounded, original-free guest-state classification.
    s = s.replace(FAIL, 
      """  grep -E '^V136_SECOND_PASS pc=8052f830 lr=80520970 status=[0-9]{1,3} r3=[0-9]{1,10} eq=[01] disable=[01] restore=[01] route=[01]$' "$work/private-native.log" | sort -u || true
""" + FAIL, 1)
    s = s.replace(DONE, DONE + """
grep -E '^V136_SECOND_PASS pc=8052f830 lr=80520970 status=1 r3=1 eq=1 disable=1 restore=1 route=1$' "$log" | sort -u
test "$(grep -Ec '^V136_SECOND_PASS pc=8052f830 lr=80520970 status=1 r3=1 eq=1 disable=1 restore=1 route=1$' "$log")" -eq 16
echo 'V136_SECOND_RETRY verified=1'
""", 1)
    return s

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
