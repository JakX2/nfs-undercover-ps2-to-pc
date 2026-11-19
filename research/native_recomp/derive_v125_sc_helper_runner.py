#!/usr/bin/env python3
"""V125 owner-original next-call runner after SC helper."""
from derive_v124_sc_second_save_runner import derive as previous
from pathlib import Path
import argparse
EDITS=[
 ("derive_v124_sc_second_save_harness.py","derive_v125_sc_helper_harness.py"),
 ("V124_TRIAL_PASS","V125_TRIAL_PASS"),
 ("V124 recovered continuous original __start->SC IOS second register-save call and successor",
  "V125 recovered continuous original __start->SC IOS SC helper continuation"),
 ("V124_STAGE native_test_passed","V125_STAGE native_test_passed"),
 ("V124_NATIVE_EXIT","V125_NATIVE_EXIT"),
 ("stage=124","stage=125")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        if a not in s:raise ValueError("V125 runner missing source anchor: "+a)
        s=s.replace(a,b)
    fail="  echo 'V125_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V125 fail marker missing")
    s=s.replace(fail,"  grep -E '^V125_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    good="echo 'V125_STAGE native_test_passed'"
    if s.count(good)!=1:raise ValueError("V125 pass marker missing")
    s=s.replace(good,good+"""
grep -Fx 'V124_NEXT_CALL pc=8051e5bc lr=8051e054 route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V125_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V125_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    old="candidate=\"$(grep -E '^V124_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(old)!=1:raise ValueError("V125 dynamic candidate anchor")
    s=s.replace(old,"candidate=\"$(grep -E '^V125_NEXT_CALL pc=[0-9a-f]{8}",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
