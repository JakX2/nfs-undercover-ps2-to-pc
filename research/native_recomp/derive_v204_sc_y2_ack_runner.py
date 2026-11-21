#!/usr/bin/env python3
"""V204 owner-original gate for authentic second-Y2 PPCCTRL W1C."""
import argparse
from pathlib import Path
from derive_v203_sc_y2_distinct_runner import derive as previous

OLD='python3 "$here/derive_v203_sc_y2_distinct_harness.py"'
NEW='python3 "$here/derive_v204_sc_y2_ack_harness.py"'
DONE="echo 'V203_SC_Y2_DISTINCT verified=1'"
PATTERN=r'^V204_Y2_ACK write=[01] w1c=[01] flag=[01] queued=[01] guest=[01] progressed=[01] sc=[01]$'
PASS=r'^V204_Y2_ACK write=1 w1c=1 flag=1 queued=1 guest=1 progressed=1 sc=1$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V204 inherited V203 native owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V204 native failure-exit anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V204_SC_Y2_ACK verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
