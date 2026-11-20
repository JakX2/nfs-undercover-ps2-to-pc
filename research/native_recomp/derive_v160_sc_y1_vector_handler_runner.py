#!/usr/bin/env python3
"""V160 sixteen native trials of original installed SC Y1 exception vector."""
import argparse
from pathlib import Path
from derive_v159_sc_y1_vector_runner import derive as previous

OLD='python3 "$here/derive_v159_sc_y1_vector_harness.py"'
NEW='python3 "$here/derive_v160_sc_y1_vector_handler_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V159_SC_Y1_VECTOR verified=1'"
ENTRY="V160_SC_VECTOR_ENTRY saved=1 regs=1 bytes=1 masked=1"
PATTERN=r'^V160_SC_VECTOR_HANDLER vector=[01] masked=[01] irq=[01] advanced=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V160_SC_VECTOR_HANDLER vector=1 masked=1 irq=1 advanced=1 pc=80526ce0 lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V160 inherited original Y1 vector runner source differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -Fx "'+ENTRY+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -Fx '{ENTRY}' "$log" | sort -u
test "$(grep -Fxc '{ENTRY}' "$log")" -eq 16
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V160_SC_VECTOR_HANDLER verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
