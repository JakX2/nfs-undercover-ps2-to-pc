#!/usr/bin/env python3
"""V139 gate owner original Wii SC request ACK, 16 trials, no game-code edits."""
import argparse
from pathlib import Path
from derive_v138_ios_request_runner import derive as previous

BEFORE='python3 "$here/derive_v138_ios_request_harness.py"'
AFTER='python3 "$here/derive_v139_sc_ios_service_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V138_REQUEST_PROBE verified=1'"
PATTERN=r'^V139_SC_IOS_ACK mount=[01] request=[01] ack=[01] queued=[01] irq=[01] fd=[01]$'

def derive(source: str) -> str:
    s=previous(source)
    if s.count(BEFORE)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V139 inherited runner selector or gate changed")
    s=s.replace(BEFORE,AFTER,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+"""
grep -Fx 'V139_SC_IOS_ACK mount=1 request=1 ack=1 queued=1 irq=1 fd=1' "$log" | sort -u
test "$(grep -Fc 'V139_SC_IOS_ACK mount=1 request=1 ack=1 queued=1 irq=1 fd=1' "$log")" -eq 16
echo 'V139_SC_ACK verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
