#!/usr/bin/env python3
"""V221 third negative Y1 IPC callback first hardware helper runner."""
import argparse
from pathlib import Path
from derive_v220_sc_y1_ipc_handler_runner import derive as previous
OLD='python3 "$here/derive_v220_sc_y1_ipc_handler_harness.py"'
NEW='python3 "$here/derive_v221_sc_y1_ipc_leaf_harness.py"'
DONE="echo 'V220_SC_Y1_IPC_HANDLER verified=1'"
PATTERN=r'^V221_NEG_LEAF call=[01] masked=[01] signal=[01] reply=[01] stepped=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V221_NEG_LEAF call=1 masked=1 signal=1 reply=1 stepped=1 sc=1 pc=(8051905c|8051906c|8051b060) lr=[0-9a-f]{8}$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V221 inherited V220 owner-original runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V221 native original failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V221_SC_Y1_IPC_LEAF verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
