#!/usr/bin/env python3
"""V126 owner-original continuation after executing post-SC GPR-save helper."""
import argparse
from pathlib import Path
from derive_v125_sc_helper_runner import derive as previous
EDITS=[
 ("derive_v125_sc_helper_harness.py","derive_v126_sc_post_gpr_harness.py"),
 ("V125_TRIAL_PASS","V126_TRIAL_PASS"),
 ("V125 recovered continuous original __start->SC IOS SC helper continuation",
  "V126 recovered continuous original __start->SC IOS post-helper GPR-save and next call"),
 ("V125_STAGE native_test_passed","V126_STAGE native_test_passed"),
 ("V125_NATIVE_EXIT","V126_NATIVE_EXIT"),
 ("stage=125","stage=126")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        if a not in s:raise ValueError("V126 runner missing source anchor: "+a)
        s=s.replace(a,b)
    fail="  echo 'V126_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V126 failure marker missing")
    s=s.replace(fail,"  grep -E '^V126_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    good="echo 'V126_STAGE native_test_passed'"
    if s.count(good)!=1:raise ValueError("V126 native success marker missing")
    s=s.replace(good,good+"""
grep -Fx 'V125_NEXT_CALL pc=80545150 lr=8051e05c route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V126_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V126_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    old="candidate=\"$(grep -E '^V125_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(old)!=1:raise ValueError("V126 original-free candidate marker differs")
    s=s.replace(old,"candidate=\"$(grep -E '^V126_NEXT_CALL pc=[0-9a-f]{8}",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
