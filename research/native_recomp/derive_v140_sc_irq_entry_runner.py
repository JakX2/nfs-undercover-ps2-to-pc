#!/usr/bin/env python3
"""V140 require actual external vector entry from owner-original SC IPC ACK."""
import argparse
from pathlib import Path
from derive_v139_sc_ios_service_runner import derive as previous

OLD='python3 "$here/derive_v139_sc_ios_service_harness.py"'
NEW='python3 "$here/derive_v140_sc_irq_entry_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V139_SC_ACK verified=1'"
PATTERN=r'^V140_SC_IRQ_ENTRY pending=[01] vector=[01] saved=[01] regs=[01] queued=[01]$'
PASS="V140_SC_IRQ_ENTRY pending=1 vector=1 saved=1 regs=1 queued=1"

def derive(source: str) -> str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V140 original native service runner source anchors changed")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -Fx '{PASS}' "$log" | sort -u
test "$(grep -Fxc '{PASS}' "$log")" -eq 16
echo 'V140_SC_IRQ_ENTRY verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
