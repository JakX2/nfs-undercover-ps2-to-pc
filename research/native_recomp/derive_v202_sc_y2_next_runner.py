#!/usr/bin/env python3
"""V202 native second Y2 IPC helper return and next handler-owned guest call."""
import argparse
from pathlib import Path
from derive_v201_sc_y2_leaf_runner import derive as previous

OLD='python3 "$here/derive_v201_sc_y2_leaf_harness.py"'
NEW='python3 "$here/derive_v202_sc_y2_next_harness.py"'
DONE="echo 'V201_SC_Y2_LEAF verified=1'"
PATTERN=r'^V202_Y2_NEXT first=[01] caller=[01] stepped=[01] masked=[01] queued=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V202_Y2_NEXT first=1 caller=1 stepped=1 masked=1 queued=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V202 inherited owner-original V201 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V202 native failure-exit anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V202_SC_Y2_NEXT verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
