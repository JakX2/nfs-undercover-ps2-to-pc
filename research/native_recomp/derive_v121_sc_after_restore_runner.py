#!/usr/bin/env python3
"""V121 dynamic original-call checkpoint after verified SC X1 submission."""
import argparse
from pathlib import Path
from derive_v120_sc_x1_sleep_runner import derive as previous

EDITS=[
 ("derive_v120_sc_x1_sleep_harness.py","derive_v121_sc_after_restore_harness.py"),
 ("V120_TRIAL_PASS","V121_TRIAL_PASS"),
 ("V120 recovered continuous original __start->SC IOS X1 submission and interrupt-restore call entry assertions",
  "V121 recovered continuous original __start->SC IOS post-X1 continuation call assertions"),
 ("V120_STAGE native_test_passed","V121_STAGE native_test_passed"),
 ("V120_NATIVE_EXIT","V121_NATIVE_EXIT"),
 ("stop=0x805265d4","stop=0x[0-9a-f]{8}")
]

def derive(source):
    s=previous(source)
    for a,b in EDITS:
        if a not in s:raise ValueError("V121 runner missing source anchor: "+a)
        s=s.replace(a,b)
    fail="  echo 'V121_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V121 failure marker missing")
    diag=(
      "  grep -E '^V121_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$'"
      ' "$work/private-native.log" | sort -u || true\n'
    )
    s=s.replace(fail,diag+fail,1)
    good="echo 'V121_STAGE native_test_passed'"
    if s.count(good)!=1:raise ValueError("V121 success marker missing")
    s=s.replace(good,good+"""
grep -E '^V121_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V121_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    old="echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805265D4 stage=120'"
    if s.count(old)!=1:raise ValueError("V121 previous progress marker differs")
    new="""candidate="$(grep -E '^V121_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | tail -n 1 | cut -d' ' -f2 | cut -d= -f2)"
[[ "$candidate" =~ ^[0-9a-f]{8}$ ]]
echo "BOOT_PROGRESS entry=0x8000403C pc=0x${candidate^^} stage=121" """
    s=s.replace(old,new.rstrip(),1)
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
