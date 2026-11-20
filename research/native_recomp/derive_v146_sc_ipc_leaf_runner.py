#!/usr/bin/env python3
"""V146 gate original SC IPC leaf entry in sixteen owner-private native trials."""
import argparse
from pathlib import Path
from derive_v145_sc_ipc_handler_runner import derive as previous

OLD='python3 "$here/derive_v145_sc_ipc_handler_harness.py"'
NEW='python3 "$here/derive_v146_sc_ipc_leaf_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V145_SC_IPC verified=1'"
PATTERN=r'^V146_SC_IPC_LEAF call=[01] masked=[01] queued=[01] stepped=[01] target=(8051905c|8051906c|8051b060)$'
PASS=r'^V146_SC_IPC_LEAF call=1 masked=1 queued=1 stepped=1 target=(8051905c|8051906c|8051b060)$'

def derive(source):
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V146 native runner source gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V146_SC_IPC_LEAF verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
