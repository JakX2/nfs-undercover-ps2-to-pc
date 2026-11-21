#!/usr/bin/env python3
"""V200 original Wii second Y2 scheduler-disable to registered IPC handler."""
import argparse
from pathlib import Path
from derive_v199_sc_y2_disable_runner import derive as previous

OLD='python3 "$here/derive_v199_sc_y2_disable_harness.py"'
NEW='python3 "$here/derive_v200_sc_y2_ipc_harness.py"'
DONE="echo 'V199_SC_Y2_DISABLE verified=1'"
PATTERN=r'^V200_Y2_IPC dispatch=[01] context=[01] registered=[01] masked=[01] pending=[01] progressed=[01] resume=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V200_Y2_IPC dispatch=1 context=1 registered=1 masked=1 pending=1 progressed=1 resume=1 pc=80519318 lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V200 inherited V199 native runner source changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V200 inherited native failure-exit anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V200_SC_Y2_IPC verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
