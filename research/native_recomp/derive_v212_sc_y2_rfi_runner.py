#!/usr/bin/env python3
"""V212 original second-Y2 OSLoadContext/RFI owner-native runner."""
import argparse
from pathlib import Path
from derive_v211_sc_y2_resched_next_runner import derive as previous

OLD='python3 "$here/derive_v211_sc_y2_resched_next_harness.py"'
NEW='python3 "$here/derive_v212_sc_y2_rfi_harness.py"'
DONE="echo 'V211_SC_Y2_RESCHED_NEXT verified=1'"
PATTERN=r'^V212_Y2_RFI pc=[01] msr=[01] regs=[01] irq_down=[01] queue=[01] open=[01] coherent=[01] sc=[01] ee=[01] idle=[01] thread=[01]$'
PASS=r'^V212_Y2_RFI pc=1 msr=1 regs=1 irq_down=1 queue=1 open=1 coherent=1 sc=1 ee=[01] idle=[01] thread=[01]$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V212 inherited V211 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V212 original native failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V212_SC_Y2_RFI verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
