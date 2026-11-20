#!/usr/bin/env python3
"""V164 require 16 owner-original SC Y1 scheduler-disable nested helper trials."""
import argparse
from pathlib import Path
from derive_v163_sc_y1_disable_runner import derive as previous

OLD='python3 "$here/derive_v163_sc_y1_disable_harness.py"'
NEW='python3 "$here/derive_v164_sc_y1_nested_helper_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V163_SC_Y1_DISABLE verified=1'"
PATTERN=r'^V164_SC_Y1_NESTED irq=[01] reply=[01] masked=[01] guest=[01] caller=[01] target=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V164_SC_Y1_NESTED irq=1 reply=1 masked=1 guest=1 caller=1 target=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V164 owner-private original runner predecessor gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V164_SC_Y1_NESTED verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
