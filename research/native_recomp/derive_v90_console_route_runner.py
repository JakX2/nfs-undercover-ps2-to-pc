#!/usr/bin/env python3
"""Derive V90 runner from V89."""
import argparse
from pathlib import Path
from derive_v89_post_stm_runner import derive as previous

EDITS = [
  [
    "V89_SOURCE_ROOT",
    "V90_SOURCE_ROOT"
  ],
  [
    "run_v89_continuous_post_stm.sh",
    "run_v90_continuous_console_route.sh"
  ],
  [
    "derive_v89_post_stm_harness.py",
    "derive_v90_console_route_harness.py"
  ],
  [
    "V89 recovered continuous original __start->post STM console query assertions; mode=owner trials=16 stop=0x8051fd44",
    "V90 recovered continuous original __start->post STM original dependency assertions; mode=owner trials=16 stop=0x(8051e7e4|8052f94c)"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051FD44 stage=89'",
    "awk '/^V90_ROUTE_TARGET mode=[0-3] pc=(8051e7e4|8052f94c)$/ { print \"BOOT_PROGRESS entry=0x8000403C pc=0x\" toupper(substr($3,4)) \" stage=90\" }' \"$work/private-native.log\" | sort -u"
  ],
  [
    "PASS: original Wii continuous __start entered post-STM subsystem and original console query",
    "PASS: original Wii continuous __start followed original console classification to next subsystem dependency"
  ],
  [
    "  echo 'V89 post-STM original subsystem failed; details withheld' >&2",
    "  grep -E '^V90_CONSOLE_ROUTE route=[01] abi=[01] console=[01] queue=[01] devices=[01] pending=[01]$|^V90_ROUTE_TARGET mode=[0-3] pc=(8051e7e4|8052f94c)$' \"$work/private-native.log\" | sort -u || true\n  echo 'V90 original console route failed; details withheld' >&2"
  ],
  [
    "echo 'V89_STAGE native_test_passed'",
    "echo 'V90_STAGE native_test_passed'\ngrep -E '^V90_CONSOLE_ROUTE route=[01] abi=[01] console=[01] queue=[01] devices=[01] pending=[01]$|^V90_ROUTE_TARGET mode=[0-3] pc=(8051e7e4|8052f94c)$' \"$work/private-native.log\" | sort -u\nfor mode in 0 1 2 3; do\n  [[ $(grep -Ec \"^V90_ROUTE_TARGET mode=$mode pc=(8051e7e4|8052f94c)$\" \"$work/private-native.log\") == 4 ]]\ndone"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V89_STAGE", "V90_STAGE").replace("V89_TRIAL_PASS", "V90_TRIAL_PASS")

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
