#!/usr/bin/env python3
"""V159 require genuine pending SC reply IRQ vector entry in 16 owner trials."""
import argparse
from pathlib import Path
from derive_v158_sc_rfi_restore_runner import derive as previous

OLD='python3 "$here/derive_v158_sc_rfi_restore_harness.py"'
NEW='python3 "$here/derive_v159_sc_y1_vector_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V158_SC_RFI verified=1'"
PATTERN=r'^V159_SC_Y1_VECTOR pending=[01] safe=[01] entered=[01] vector=[01] regs=[01] masked=[01]$'
PASS="V159_SC_Y1_VECTOR pending=1 safe=1 entered=1 vector=1 regs=1 masked=1"

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V159 native wrapper inherited gate count differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -Fx '{PASS}' "$log" | sort -u
test "$(grep -Fxc '{PASS}' "$log")" -eq 16
echo 'V159_SC_Y1_VECTOR verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
