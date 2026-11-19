#!/usr/bin/env python3
"""V122 owner-original next call after translated register-save."""
from derive_v121_sc_after_restore_runner import derive as previous
from pathlib import Path
import argparse
EDITS=[
 ("derive_v121_sc_after_restore_harness.py","derive_v122_sc_post_save_harness.py"),
 ("V121_TRIAL_PASS","V122_TRIAL_PASS"),
 ("V121 recovered continuous original __start->SC IOS post-X1 continuation call assertions",
  "V122 recovered continuous original __start->SC IOS register-save and next call assertions"),
 ("V121_STAGE native_test_passed","V122_STAGE native_test_passed"),
 ("V121_NATIVE_EXIT","V122_NATIVE_EXIT"),
 ("stage=121","stage=122")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        if a not in s:raise ValueError("V122 runner missing source anchor: "+a)
        s=s.replace(a,b)
    fail="  echo 'V122_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V122 native failure marker missing")
    s=s.replace(fail,"  grep -E '^V122_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    good="echo 'V122_STAGE native_test_passed'"
    if s.count(good)!=1:raise ValueError("V122 native pass marker missing")
    s=s.replace(good,good+"""
grep -Fx 'V121_NEXT_CALL pc=80545150 lr=80519934 route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V122_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V122_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    target="candidate=\"$(grep -E '^V121_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(target)!=1:raise ValueError("V122 candidate anchor differs")
    s=s.replace(target,"candidate=\"$(grep -E '^V122_NEXT_CALL pc=[0-9a-f]{8}",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
