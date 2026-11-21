#!/usr/bin/env python3
"""V198 original second IOS Y2 dispatcher to timebase guest call."""
import argparse
from pathlib import Path
from derive_v197_sc_y2_dispatch_runner import derive as previous

OLD='python3 "$here/derive_v197_sc_y2_dispatch_harness.py"'
NEW='python3 "$here/derive_v198_sc_y2_time_harness.py"'
DONE="echo 'V197_SC_Y2_DISPATCH verified=1'"
PATTERN=r'^V198_Y2_TIME time=[01] masked=[01] pending=[01] progressed=[01] resume=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V198_Y2_TIME time=1 masked=1 pending=1 progressed=1 resume=1 pc=8052a824 lr=80526c84$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V198 native runner inherited second Y2 dispatcher gates changed")
    s=s.replace(OLD,NEW,1)
    # A failed authentic observation throws before the owner runner emits its
    # native-success line. Print only the bounded, original-free V198 flags
    # from the private log at the inherited failure exit.
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V198 owner-native failure-exit anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\\n'+fail,1)
    success='  echo "V186_NATIVE_SUCCESS pre=$v186_pre ack=$v186_ack state=$v186_state previous=$v186_v185"'
    if s.count(success)!=1:
        raise ValueError("V198 native trial diagnostic anchor changed")
    diag=(
        '  v198_count=$(grep -Ec "^V198_Y2_TIME " "$work/private-native.log" || true)\n'
        '  [[ "$v198_count" =~ ^[0-9]{1,2}$ ]] || exit 1\n'
        '  echo "V198_ENTRY_COUNT lines=$v198_count"\n'
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
    )
    s=s.replace(success,success+"\n"+diag,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V198_SC_Y2_TIME verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
