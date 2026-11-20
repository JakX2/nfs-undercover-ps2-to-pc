#!/usr/bin/env python3
"""V133 owner original SC status byte observer and prior native assertions."""
import argparse
from pathlib import Path
from derive_v131_retry_state_runner import derive as previous
def derive(source):
    s=previous(source)
    old='python3 "$here/derive_v131_retry_state_harness.py"'
    if s.count(old)!=1:raise ValueError("V133 harness selector differs")
    s=s.replace(old,'python3 "$here/derive_v133_sc_sda_harness.py"',1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V133 failure reporter missing")
    s=s.replace(fail,
      "  grep -E '^V133_STATUS_BYTE mapped=[01] value=[0-9]{1,3} r3=[0-9]{1,10} eq=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    done="echo 'V131_STATE_PROBE verified=1'"
    if s.count(done)!=1:raise ValueError("V133 inherited checkpoint differs")
    s=s.replace(done,done+"""
grep -E '^V133_STATUS_BYTE mapped=1 value=[0-9]{1,3} r3=1 eq=1$' "$log" | sort -u
test "$(grep -Ec '^V133_STATUS_BYTE mapped=1 value=[0-9]{1,3} r3=1 eq=1$' "$log")" -eq 16
echo 'V133_STATUS_PROBE verified=1'
""",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as o:o.write(derive(a.source.read_text(encoding="utf-8")))
