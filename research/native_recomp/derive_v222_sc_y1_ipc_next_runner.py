#!/usr/bin/env python3
"""V222 genuine third negative IOS Y1 IPC successive native callee runner."""
import argparse
from pathlib import Path
from derive_v221_sc_y1_ipc_leaf_runner import derive as previous
OLD='python3 "$here/derive_v221_sc_y1_ipc_leaf_harness.py"'
NEW='python3 "$here/derive_v222_sc_y1_ipc_next_harness.py"'
DONE="echo 'V221_SC_Y1_IPC_LEAF verified=1'"
PATTERN=r'^V222_NEG_NEXT guest=[01] caller=[01] reply=[01] masked=[01] coherent=[01] irq=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V222_NEG_NEXT guest=1 caller=1 reply=1 masked=1 coherent=1 irq=[01] sc=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V222 original V221 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V222 original native failure hook changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V222_SC_Y1_IPC_NEXT verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
