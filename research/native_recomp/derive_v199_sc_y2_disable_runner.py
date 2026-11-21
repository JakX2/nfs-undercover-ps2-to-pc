#!/usr/bin/env python3
"""V199 original second IOS Y2 timebase into scheduler disable."""
import argparse
from pathlib import Path
from derive_v198_sc_y2_time_runner import derive as previous

OLD='python3 "$here/derive_v198_sc_y2_time_harness.py"'
NEW='python3 "$here/derive_v199_sc_y2_disable_harness.py"'
DONE="echo 'V198_SC_Y2_TIME verified=1'"
PATTERN=r'^V199_Y2_DISABLE route=[01] masked=[01] pending=[01] progressed=[01] resume=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V199_Y2_DISABLE route=1 masked=1 pending=1 progressed=1 resume=1 pc=805293f8 lr=80526c98$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V199 inherited native original timebase runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V199 native failure-exit diagnostic anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V199_SC_Y2_DISABLE verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
