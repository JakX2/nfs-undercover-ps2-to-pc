#!/usr/bin/env python3
"""V142 require owner-native original SC interrupt dispatcher entry in every trial."""
import argparse
from pathlib import Path
from derive_v141_sc_vector_runner import derive as previous

OLD='python3 "$here/derive_v141_sc_vector_harness.py"'
NEW='python3 "$here/derive_v142_sc_dispatch_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V141_SC_VECTOR verified=1'"
PATTERN=r'^V142_SC_DISPATCH route=[01] regs=[01] status=[01] pending=[01]$'
PASS="V142_SC_DISPATCH route=1 regs=1 status=1 pending=1"

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V142 original SC dispatch runner anchors changed")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -Fx '{PASS}' "$log" | sort -u
test "$(grep -Fxc '{PASS}' "$log")" -eq 16
echo 'V142_SC_DISPATCH verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
