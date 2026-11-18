#!/usr/bin/env python3
"""Derive V91 runner from V90."""
import argparse
from pathlib import Path
from derive_v90_console_route_runner import derive as previous

EDITS = [
  [
    "V90_SOURCE_ROOT",
    "V91_SOURCE_ROOT"
  ],
  [
    "run_v90_continuous_console_route.sh",
    "run_v91_continuous_resource_open.sh"
  ],
  [
    "derive_v90_console_route_harness.py",
    "derive_v91_resource_open_harness.py"
  ],
  [
    "derive_v89_post_stm_generator.py",
    "derive_v91_resource_open_generator.py"
  ],
  [
    "echo 'V90_STAGE geometry_verified'",
    "python3 \"$here/restore_resource_init_v91.py\" \"$work/private.dol\" \"$owner\" \"$work/resource-init.dol\" > \"$work/extend-resource.log\" 2>&1 || {\n    echo 'V91 original resource fixture extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/resource-init.dol\" \"$work/private.dol\"\necho 'V90_STAGE geometry_verified'"
  ],
  [
    "V90 recovered continuous original __start->post STM original dependency assertions; mode=owner trials=16 stop=0x(8051e7e4|8052f94c)",
    "V91 recovered continuous original __start->next IOS resource open assertions; mode=owner trials=16 stop=0x80519944"
  ],
  [
    "awk '/^V90_ROUTE_TARGET mode=[0-3] pc=(8051e7e4|8052f94c)$/ { print \"BOOT_PROGRESS entry=0x8000403C pc=0x\" toupper(substr($3,4)) \" stage=90\" }' \"$work/private-native.log\" | sort -u",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80519944 stage=91'"
  ],
  [
    "PASS: original Wii continuous __start followed original console classification to next subsystem dependency",
    "PASS: original Wii continuous __start reached next original IOS resource open"
  ],
  [
    "  echo 'V90 original console route failed; details withheld' >&2",
    "  grep -E '^V91_RESOURCE_BUFFER route=[01] bounds=[01]$|^V91_RESOURCE_OPEN route=[01] abi=[01] path=[01] devices=[01] pending=[01] kind=[0-8]$|^V91_LITERAL count=[0-3]$|^V91_PATH_DIAGNOSTIC length=[0-9]{1,2} mem2=[01]$' \"$work/private-native.log\" | sort -u || true\n  echo 'V91 original resource initialization failed; details withheld' >&2"
  ],
  [
    "echo 'V90_STAGE native_test_passed'",
    "echo 'V91_STAGE native_test_passed'\ngrep -E '^V91_RESOURCE_BUFFER route=[01] bounds=[01]$|^V91_RESOURCE_OPEN route=[01] abi=[01] path=[01] devices=[01] pending=[01] kind=[0-8]$|^V91_LITERAL count=[0-3]$|^V91_PATH_DIAGNOSTIC length=[0-9]{1,2} mem2=[01]$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    return source.replace("V90_STAGE", "V91_STAGE").replace("V90_TRIAL_PASS", "V91_TRIAL_PASS")

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
