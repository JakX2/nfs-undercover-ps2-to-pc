#!/usr/bin/env python3
"""V217 original Wii negative third Y1 exception to IRQ dispatch."""
import argparse
from pathlib import Path
from derive_v216_sc_y1_handler_runner import derive as previous

OLD='python3 "$here/derive_v216_sc_y1_handler_harness.py"'
NEW='python3 "$here/derive_v217_sc_y1_dispatch_harness.py"'
DONE="echo 'V216_SC_Y1_HANDLER verified=1'"
PATTERN=r'^V217_NEG_DISPATCH index=[01] context=[01] masked=[01] irq=[01] reply=[01] guest=[01] saved=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V217_NEG_DISPATCH index=1 context=1 masked=1 irq=1 reply=1 guest=1 saved=[01] pc=80526a3c lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V217 inherited V216 original owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V217 native failure hook changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V217_SC_Y1_NEG_DISPATCH verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
