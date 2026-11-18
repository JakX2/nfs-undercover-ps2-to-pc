#!/usr/bin/env python3
"""Derive V89 runner from V88."""
import argparse
from pathlib import Path
from derive_v88_stm_return_runner import derive as previous

EDITS = [
  [
    "V88_SOURCE_ROOT",
    "V89_SOURCE_ROOT"
  ],
  [
    "run_v88_continuous_stm_return.sh",
    "run_v89_continuous_post_stm.sh"
  ],
  [
    "derive_v88_stm_return_harness.py",
    "derive_v89_post_stm_harness.py"
  ],
  [
    "derive_v86_stm_ioctl_generator.py",
    "derive_v89_post_stm_generator.py"
  ],
  [
    "echo 'V88_STAGE geometry_verified'",
    "python3 \"$here/restore_post_stm_v89.py\" \"$work/private.dol\" \"$owner\" \"$work/post-stm.dol\" > \"$work/extend-post-stm.log\" 2>&1 || {\n    echo 'V89 original post-STM fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/post-stm.dol\" \"$work/private.dol\"\necho 'V88_STAGE geometry_verified'"
  ],
  [
    "V88 recovered continuous original __start->STM return after deferred ACK assertions; mode=owner trials=16 stop=0x80520968",
    "V89 recovered continuous original __start->post STM console query assertions; mode=owner trials=16 stop=0x8051fd44"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x80520968 stage=88",
    "BOOT_PROGRESS entry=0x8000403C pc=0x8051FD44 stage=89"
  ],
  [
    "PASS: original Wii continuous __start returned from original STM initialization",
    "PASS: original Wii continuous __start entered post-STM subsystem and original console query"
  ],
  [
    "  echo 'V88 original STM return failed; details withheld' >&2",
    "  grep -E '^V89_SUBSYSTEM route=[01] queue=[01] abi=[01] version=[01] pending=[01]$|^V89_DEPENDENCY pc=80[45][0-9a-f]{5} lr=80[45][0-9a-f]{5}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V89 post-STM original subsystem failed; details withheld' >&2"
  ],
  [
    "echo 'V88_STAGE native_test_passed'",
    "echo 'V89_STAGE native_test_passed'\ngrep -E '^V89_SUBSYSTEM route=[01] queue=[01] abi=[01] version=[01] pending=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V88_STAGE", "V89_STAGE").replace("V88_TRIAL_PASS", "V89_TRIAL_PASS")

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
