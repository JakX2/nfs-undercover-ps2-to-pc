#!/usr/bin/env python3
"""Derive V104 runner from V103."""
import argparse
from pathlib import Path
from derive_v103_sc_async_entry_runner import derive as previous

EDITS = [
  [
    "V103_SOURCE_ROOT",
    "V104_SOURCE_ROOT"
  ],
  [
    "run_v103_continuous_sc_async_entry.sh",
    "run_v104_continuous_sc_async_submit.sh"
  ],
  [
    "derive_v103_sc_async_entry_harness.py",
    "derive_v104_sc_async_submit_harness.py"
  ],
  [
    "derive_v103_sc_async_entry_generator.py",
    "derive_v104_sc_async_submit_generator.py"
  ],
  [
    "echo 'V103_STAGE geometry_verified'",
    "python3 \"$here/restore_sc_async_submit_v104.py\" \"$work/private.dol\" \"$owner\" \"$work/sc-async-submit.dol\" > \"$work/extend-sc-async-submit.log\" 2>&1 || {\n    echo 'V104 original IOS_OpenAsync body extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/sc-async-submit.dol\" \"$work/private.dol\"\necho 'V103_STAGE geometry_verified'"
  ],
  [
    "V103 recovered continuous original __start->IOS_OpenAsync entry assertions; mode=owner trials=16 stop=0x8051982c",
    "V104 recovered continuous original __start->IOS_OpenAsync native submit assertions; mode=owner trials=16 stop=0x805195ec"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051982C stage=103'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=104'"
  ],
  [
    "PASS: original Wii continuous __start executed SC asynchronous wrapper into IOS_OpenAsync",
    "PASS: original Wii continuous __start constructed authentic IOS_OpenAsync request"
  ],
  [
    "  echo 'V103 original SC async open entry failed; details withheld' >&2",
    "  grep -E '^V104_ASYNC_SAVE route=[01]$|^V104_ASYNC_CACHE bounded=[01]$|^V104_ASYNC_SUBMIT route=[01] request=[01] mode=[01] path=[01] abi=[01] prior=[01]$|^V104_ASYNC_SYSCALL order=[01] lines=[01]$|^V104_FAIL_HOOK pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V104_FALLTHROUGH pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8} phase=[0-9]{1,2} cache=[0-9]{1,2}$|^V104_DEPENDENCY pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V104_TRACE seq=[0-9]{1,2} pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V104 original IOS_OpenAsync request submit failed; details withheld' >&2"
  ],
  [
    "echo 'V103_STAGE native_test_passed'",
    "echo 'V104_STAGE native_test_passed'\ngrep -E '^V104_ASYNC_SAVE route=[01]$|^V104_ASYNC_CACHE bounded=[01]$|^V104_ASYNC_SUBMIT route=[01] request=[01] mode=[01] path=[01] abi=[01] prior=[01]$|^V104_ASYNC_SYSCALL order=[01] lines=[01]$|^V104_FAIL_HOOK pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V104_FALLTHROUGH pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8} phase=[0-9]{1,2} cache=[0-9]{1,2}$|^V104_DEPENDENCY pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V104_TRACE seq=[0-9]{1,2} pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V103_STAGE", "V104_STAGE").replace("V103_TRIAL_PASS", "V104_TRIAL_PASS")

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
