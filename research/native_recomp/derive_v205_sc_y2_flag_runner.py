#!/usr/bin/env python3
"""V205 native second Y2 Hollywood PPC_FLAG original guest W1C."""
import argparse
from pathlib import Path
from derive_v204_sc_y2_ack_runner import derive as previous

OLD='python3 "$here/derive_v204_sc_y2_ack_harness.py"'
NEW='python3 "$here/derive_v205_sc_y2_flag_harness.py"'
DONE="echo 'V204_SC_Y2_ACK verified=1'"
PATTERN=r'^V205_Y2_FLAG write=[01] cleared=[01] ctrl=[01] irq_down=[01] queued=[01] guest=[01] progressed=[01] sc=[01]$'
PASS=r'^V205_Y2_FLAG write=1 cleared=1 ctrl=1 irq_down=1 queued=1 guest=1 progressed=1 sc=1$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V205 inherited original V204 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V205 native failure-exit anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V205_SC_Y2_FLAG verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
