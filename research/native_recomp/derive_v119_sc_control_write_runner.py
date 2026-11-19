#!/usr/bin/env python3
"""V119 verify authentic original IPC control-register read return and next write helper."""
import argparse
from pathlib import Path
from derive_v118_sc_async_mailbox_runner import derive as previous

EDITS=[
 ("derive_v118_sc_async_mailbox_harness.py","derive_v119_sc_control_write_harness.py"),
 ("V118_TRIAL_PASS","V119_TRIAL_PASS"),
 ("V118 recovered continuous original __start->SC IOS control-register read entry assertions",
  "V119 recovered continuous original __start->SC IOS control-register read return and write-helper entry assertions"),
 ("stop=0x8051905c","stop=0x8051906c"),
 ("V118_STAGE native_test_passed","V119_STAGE native_test_passed"),
 ("V118_NATIVE_EXIT","V119_NATIVE_EXIT"),
 ("BOOT_PROGRESS entry=0x8000403C pc=0x8051905C stage=118",
  "BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=119")
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        if old not in s:
            raise ValueError("V119 runner source anchor missing: "+old)
        s=s.replace(old,new)
    fail="  echo 'V119_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V119 failure marker missing")
    diagnostic=(
        "  grep -E '^V119_CTRL_WRITE_ENTRY route=[01] reads=[01] wire=[01] abi=[01] prior=[01]$'"
        ' "$work/private-native.log" | sort -u || true\n'
    )
    s=s.replace(fail,diagnostic+fail,1)
    good="echo 'V119_STAGE native_test_passed'"
    if s.count(good)!=1:raise ValueError("V119 success marker missing")
    s=s.replace(good,good+"""
grep -Fx 'V119_CTRL_WRITE_ENTRY route=1 reads=1 wire=1 abi=1 prior=1' "$log" """.rstrip(),1)
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as output:
        output.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
