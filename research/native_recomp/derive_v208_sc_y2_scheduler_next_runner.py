#!/usr/bin/env python3
"""V208 original second Y2 post-IRQ scheduler successor."""
import argparse
from pathlib import Path
from derive_v207_sc_y2_helper_next_runner import derive as previous

OLD='python3 "$here/derive_v207_sc_y2_helper_next_harness.py"'
NEW='python3 "$here/derive_v208_sc_y2_scheduler_next_harness.py"'
DONE="echo 'V207_SC_Y2_HELPER_NEXT verified=1'"
PATTERN=r'^V208_Y2_SCHED y2=[01] irq_down=[01] queue=[01] open=[01] replied=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] sc=[0-9]{1,3} ee=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V208_Y2_SCHED y2=1 irq_down=[01] queue=[01] open=[01] replied=[01] guest=1 caller=1 coherent=1 mapped=1 sc=[0-9]{1,3} ee=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V208 inherited owner V207 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V208 native failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V208_SC_Y2_SCHED_NEXT verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
