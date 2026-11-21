#!/usr/bin/env python3
"""V197 original Wii second Y2 exception handler to native dispatcher."""
import argparse
from pathlib import Path
from derive_v196_sc_y2_vector_runner import derive as previous

OLD='python3 "$here/derive_v196_sc_y2_vector_harness.py"'
NEW='python3 "$here/derive_v197_sc_y2_dispatch_harness.py"'
DONE="echo 'V196_SC_Y2_VECTOR verified=1'"
PATTERN=r'^V197_Y2_DISPATCH route=[01] regs=[01] status=[01] pending=[01] progressed=[01] resume=[0-9a-f]{8} pc=[0-9a-f]{8}$'
PASS=r'^V197_Y2_DISPATCH route=1 regs=1 status=1 pending=1 progressed=1 resume=8052f830 pc=80526a3c$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V197 second Y2 owner runner inherited V196 gates changed")
    s=s.replace(OLD,NEW,1)
    success='  echo "V186_NATIVE_SUCCESS pre=$v186_pre ack=$v186_ack state=$v186_state previous=$v186_v185"'
    if s.count(success)!=1:
        raise ValueError("V197 inherited native trial checkpoint changed")
    diag=(
        '  v197_count=$(grep -Ec "^V197_Y2_DISPATCH " "$work/private-native.log" || true)\n'
        '  [[ "$v197_count" =~ ^[0-9]{1,2}$ ]] || exit 1\n'
        '  echo "V197_ENTRY_COUNT lines=$v197_count"\n'
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
    )
    s=s.replace(success,success+"\n"+diag,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V197_SC_Y2_DISPATCH verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
