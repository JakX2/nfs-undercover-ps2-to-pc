#!/usr/bin/env python3
"""V129 continue original Wii interrupt-disable and verify successor call."""
import argparse
from pathlib import Path
from derive_v128_next_function_runner import derive as previous
def derive(source):
    s=previous(source)
    for old,new in (
      ('python3 "$here/derive_v128_next_function_harness.py"',
       'python3 "$here/derive_v129_irq_disable_harness.py"'),
      ("V128_TRIAL_PASS","V129_TRIAL_PASS"),
      ("V128_STAGE native_test_passed","V129_STAGE native_test_passed"),
      ("V128_NATIVE_EXIT","V129_NATIVE_EXIT"),
      ("stage=128","stage=129")
    ):
        if old not in s:raise ValueError("V129 runner inherited checkpoint missing: "+old)
        s=s.replace(old,new)
    old="candidate=\"$(grep -E '^V128_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(old)!=1:raise ValueError("V129 original successor candidate anchor differs")
    s=s.replace(old,"candidate=\"$(grep -E '^V129_NEXT_CALL pc=[0-9a-f]{8}",1)
    fail="  echo 'V129_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V129 native failure boundary differs")
    s=s.replace(fail,"  grep -E '^V129_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    done="echo 'V129_STAGE native_test_passed'"
    if s.count(done)!=1:raise ValueError("V129 test-pass gate missing")
    s=s.replace(done,done+"""
grep -Fx 'V128_NEXT_CALL pc=805265ac lr=8052f84c route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V129_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V129_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    if s.count("V128_NATIVE_COUNTS")!=1:raise ValueError("V129 prior native summary differs")
    s=s.replace("V128_NATIVE_COUNTS","V129_NATIVE_COUNTS",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
