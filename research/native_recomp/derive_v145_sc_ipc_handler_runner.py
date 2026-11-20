#!/usr/bin/env python3
"""V145 require authentic registered Wii SC IPC handler entry in all trials."""
import argparse
from pathlib import Path
from derive_v144_sc_irq_disable_runner import derive as previous
OLD='python3 "$here/derive_v144_sc_irq_disable_harness.py"'
NEW='python3 "$here/derive_v145_sc_ipc_handler_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V144_SC_DISABLE verified=1'"
PATTERN=r'^V145_SC_IPC dispatch=[01] context=[01] masked=[01] pending=[01] progressed=[01]$'
PASS="V145_SC_IPC dispatch=1 context=1 masked=1 pending=1 progressed=1"
def derive(source):
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V145 inherited owner-native runner gate differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -Fx '{PASS}' "$log" | sort -u
test "$(grep -Fxc '{PASS}' "$log")" -eq 16
echo 'V145_SC_IPC verified=1'
""",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
