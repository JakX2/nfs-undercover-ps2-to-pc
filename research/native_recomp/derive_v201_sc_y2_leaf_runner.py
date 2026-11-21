#!/usr/bin/env python3
"""V201 owner-original gate for the first second-Y2 IPC handler helper."""
import argparse
from pathlib import Path
from derive_v200_sc_y2_ipc_runner import derive as previous

OLD='python3 "$here/derive_v200_sc_y2_ipc_harness.py"'
NEW='python3 "$here/derive_v201_sc_y2_leaf_harness.py"'
DONE="echo 'V200_SC_Y2_IPC verified=1'"
PATTERN=r'^V201_Y2_LEAF call=[01] masked=[01] queued=[01] stepped=[01] prior=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V201_Y2_LEAF call=1 masked=1 queued=1 stepped=1 prior=1 pc=(8051905c|8051906c|8051b060) lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V201 inherited V200 original native runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V201 native failure-exit anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V201_SC_Y2_LEAF verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
