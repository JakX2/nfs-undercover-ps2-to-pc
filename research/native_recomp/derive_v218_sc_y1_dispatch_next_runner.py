#!/usr/bin/env python3
"""V218 native original negative Y1 dispatcher next-function runner."""
import argparse
from pathlib import Path
from derive_v217_sc_y1_dispatch_runner import derive as previous
OLD='python3 "$here/derive_v217_sc_y1_dispatch_harness.py"'
NEW='python3 "$here/derive_v218_sc_y1_dispatch_next_harness.py"'
DONE="echo 'V217_SC_Y1_NEG_DISPATCH verified=1'"
PATTERN=r'^V218_NEG_NEXT irq=[01] reply=[01] guest=[01] caller=[01] masked=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V218_NEG_NEXT irq=1 reply=1 guest=1 caller=1 masked=1 sc=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V218 native V217 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V218 original-native error anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V218_SC_Y1_DISPATCH_NEXT verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
