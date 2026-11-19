#!/usr/bin/env python3
"""V120 verify native original X1 control write and observed thread-sleep entry."""
import argparse
from pathlib import Path
from derive_v119_sc_control_write_runner import derive as previous

EDITS = [
 ("derive_v119_sc_control_write_harness.py","derive_v120_sc_x1_sleep_harness.py"),
 ("V119_TRIAL_PASS","V120_TRIAL_PASS"),
 ("V119 recovered continuous original __start->SC IOS control-register read return and write-helper entry assertions",
  "V120 recovered continuous original __start->SC IOS X1 submission and thread-sleep call entry assertions"),
 ("stop=0x8051906c","stop=0x8052a430"),
 ("V119_STAGE native_test_passed","V120_STAGE native_test_passed"),
 ("V119_NATIVE_EXIT","V120_NATIVE_EXIT"),
 ("BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=119",
  "BOOT_PROGRESS entry=0x8000403C pc=0x8052A430 stage=120")
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        if old not in s:
            raise ValueError("V120 runner source anchor missing: "+old)
        s=s.replace(old,new)
    fail="  echo 'V120_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V120 failure marker missing")
    diag=(
        "  grep -E '^V120_X1_SLEEP_ENTRY route=[01] sent=[01] wire=[01] abi=[01] prior=[01]$"
        "|^V120_WALK seq=[0-9]{1,2} pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8} x1=[01]$'"
        ' "$work/private-native.log" | sort -u || true\n'
    )
    s=s.replace(fail,diag+fail,1)
    good="echo 'V120_STAGE native_test_passed'"
    if s.count(good)!=1:raise ValueError("V120 success marker missing")
    s=s.replace(good,good+"""
grep -Fx 'V120_X1_SLEEP_ENTRY route=1 sent=1 wire=1 abi=1 prior=1' "$log" """.rstrip(),1)
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
