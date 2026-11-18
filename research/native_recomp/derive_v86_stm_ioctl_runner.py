#!/usr/bin/env python3
"""Derive V86 runner from V85."""
import argparse
from pathlib import Path
from derive_v85_both_stm_opens_runner import derive as previous

EDITS = [
  [
    "V85_SOURCE_ROOT",
    "V86_SOURCE_ROOT"
  ],
  [
    "run_v85_continuous_both_stm_opens.sh",
    "run_v86_continuous_stm_ioctl.sh"
  ],
  [
    "derive_v85_both_stm_opens_harness.py",
    "derive_v86_stm_ioctl_harness.py"
  ],
  [
    "derive_v79_reply_generator.py",
    "derive_v86_stm_ioctl_generator.py"
  ],
  [
    "echo 'V85_STAGE geometry_verified'",
    "python3 \"$here/restore_stm_ioctl_v86.py\" \"$work/private.dol\" \"$owner\" \"$work/extended.dol\" > \"$work/extend-private.log\" 2>&1 || {\n    echo 'V86 original STM async fixture extension failed; owner details withheld' >&2; exit 1;\n  }\nmv -- \"$work/extended.dol\" \"$work/private.dol\"\necho 'V85_STAGE geometry_verified'"
  ],
  [
    "V85 recovered continuous original __start->both STM opens completed assertions; mode=owner trials=16 stop=0x805265ac",
    "V86 recovered continuous original __start->asynchronous STM submission entry assertions; mode=owner trials=16 stop=0x805195ec"
  ],
  [
    "BOOT_PROGRESS entry=0x8000403C pc=0x805265AC stage=85",
    "BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=86"
  ],
  [
    "PASS: original Wii continuous __start returned from both original STM opens",
    "PASS: original Wii continuous __start reached genuine async STM submission"
  ],
  [
    "  echo 'V85 original dual STM opens failed; details withheld' >&2",
    "  grep -E '^V86_ASYNC_ENTRY route=[01] service=[01] buffers=[01] callback=[01] idle=[01]$|^V86_ASYNC_SUBMIT route=[01] allocated=[01] flush=[01] wire=[01] idle=[01]$|^V86_DEPENDENCY pc=80[45][0-9a-f]{5} lr=80[45][0-9a-f]{5}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V86 original STM async submission failed; details withheld' >&2"
  ],
  [
    "echo 'V85_STAGE native_test_passed'",
    "echo 'V86_STAGE native_test_passed'\ngrep -E '^V86_ASYNC_ENTRY route=[01] service=[01] buffers=[01] callback=[01] idle=[01]$|^V86_ASYNC_SUBMIT route=[01] allocated=[01] flush=[01] wire=[01] idle=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V85_STAGE", "V86_STAGE").replace("V85_TRIAL_PASS", "V86_TRIAL_PASS")

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
