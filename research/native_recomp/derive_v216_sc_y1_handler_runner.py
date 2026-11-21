#!/usr/bin/env python3
"""V216 original Wii third exception vector to Y1 handler."""
import argparse
from pathlib import Path
from derive_v215_sc_y1_negative_vector_runner import derive as previous

OLD='python3 "$here/derive_v215_sc_y1_negative_vector_harness.py"'
NEW='python3 "$here/derive_v216_sc_y1_handler_harness.py"'
DONE="echo 'V215_SC_Y1_NEGATIVE_VECTOR verified=1'"
ENTRY=r'^V216_Y1_ENTRY saved=[01] regs=[01] bytes=[01] masked=[01] y1=[01] negative=[01]$'
PATTERN=r'^V216_Y1_HANDLER vector=[01] irq=[01] reply=[01] index=[01] context=[01] masked=[01] progressed=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V216_Y1_HANDLER vector=1 irq=1 reply=1 index=1 context=1 masked=1 progressed=1 pc=80526ce0 lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V216 original V215 native owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V216 original native failure hook changed")
    s=s.replace(fail,'  grep -E "'+ENTRY+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{ENTRY}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '^V216_Y1_ENTRY saved=1 regs=1 bytes=1 masked=1 y1=1 negative=1$' "$log")" -eq 16
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V216_SC_Y1_HANDLER verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
