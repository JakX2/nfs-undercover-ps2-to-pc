#!/usr/bin/env python3
"""V123 owner-original next-call runner after executing GPR helper at 0x8054514C."""
from derive_v122_sc_post_save_runner import derive as previous
from pathlib import Path
import argparse
EDITS=[
 ("derive_v122_sc_post_save_harness.py","derive_v123_sc_post_leaf_harness.py"),
 ("V122_TRIAL_PASS","V123_TRIAL_PASS"),
 ("V122 recovered continuous original __start->SC IOS register-save and next call assertions",
  "V123 recovered continuous original __start->SC IOS second helper and next call assertions"),
 ("V122_STAGE native_test_passed","V123_STAGE native_test_passed"),
 ("V122_NATIVE_EXIT","V123_NATIVE_EXIT"),
 ("stage=122","stage=123")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        if a not in s:raise ValueError("V123 runner missing anchor: "+a)
        s=s.replace(a,b)
    fail="  echo 'V123_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V123 fail marker")
    s=s.replace(fail,
        "  grep -E '^V123_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    good="echo 'V123_STAGE native_test_passed'"
    if s.count(good)!=1:raise ValueError("V123 success marker")
    s=s.replace(good,good+"""
grep -Fx 'V122_NEXT_CALL pc=8054514c lr=804f1ed4 route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V123_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V123_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    old="candidate=\"$(grep -E '^V122_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(old)!=1:raise ValueError("V123 candidate anchor")
    s=s.replace(old,"candidate=\"$(grep -E '^V123_NEXT_CALL pc=[0-9a-f]{8}",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
