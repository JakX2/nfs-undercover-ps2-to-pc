#!/usr/bin/env python3
"""V220 original third negative Y1 registered IPC callback runner."""
import argparse
from pathlib import Path
from derive_v219_sc_y1_osdisable_runner import derive as previous
OLD='python3 "$here/derive_v219_sc_y1_osdisable_harness.py"'
NEW='python3 "$here/derive_v220_sc_y1_ipc_handler_harness.py"'
DONE="echo 'V219_SC_Y1_OSDISABLE verified=1'"
PATTERN=r'^V220_NEG_IPC irq=[01] reply=[01] context=[01] caller=[01] guest=[01] masked=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V220_NEG_IPC irq=1 reply=1 context=1 caller=1 guest=1 masked=1 sc=1 pc=80519318 lr=80526cac$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V220 inherited owner-verified V219 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V220 failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V220_SC_Y1_IPC_HANDLER verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
