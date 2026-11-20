#!/usr/bin/env python3
"""V130 continuous original Wii interrupt-restore successor runner."""
import argparse
from pathlib import Path
from derive_v129_irq_disable_runner import derive as previous
def derive(source):
    s=previous(source)
    for a,b in (
      ('python3 "$here/derive_v129_irq_disable_harness.py"',
       'python3 "$here/derive_v130_irq_restore_harness.py"'),
      ("V129_TRIAL_PASS","V130_TRIAL_PASS"),
      ("V129_STAGE native_test_passed","V130_STAGE native_test_passed"),
      ("V129_NATIVE_EXIT","V130_NATIVE_EXIT"),
      ("stage=129","stage=130")
    ):
        if a not in s:raise ValueError("V130 runner checkpoint anchor differs: "+a)
        s=s.replace(a,b)
    old="candidate=\"$(grep -E '^V129_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(old)!=1:raise ValueError("V130 original next call marker differs")
    s=s.replace(old,"candidate=\"$(grep -E '^V130_NEXT_CALL pc=[0-9a-f]{8}",1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V130 native failure marker missing")
    s=s.replace(fail,"  grep -E '^V130_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    marker="echo 'V130_STAGE native_test_passed'"
    if s.count(marker)!=1:raise ValueError("V130 native pass gate missing")
    s=s.replace(marker,marker+"""
grep -Fx 'V129_NEXT_CALL pc=805265d4 lr=8052f92c route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V130_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V130_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    if s.count("V129_NATIVE_COUNTS")!=1:raise ValueError("V130 predecessor diagnostics ambiguous")
    s=s.replace("V129_NATIVE_COUNTS","V130_NATIVE_COUNTS",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
