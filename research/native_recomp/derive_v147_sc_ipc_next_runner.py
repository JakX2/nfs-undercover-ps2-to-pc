#!/usr/bin/env python3
"""V147 gate the next original SC IPC handler BL after running its first leaf."""
import argparse
from pathlib import Path
from derive_v146_sc_ipc_leaf_runner import derive as previous

OLD='python3 "$here/derive_v146_sc_ipc_leaf_harness.py"'
NEW='python3 "$here/derive_v147_sc_ipc_next_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V146_SC_IPC_LEAF verified=1'"
PATTERN=r'^V147_SC_IPC_NEXT first=[01] caller=[01] progressed=[01] masked=[01] queued=[01] irq=[01] target=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V147_SC_IPC_NEXT first=1 caller=1 progressed=1 masked=1 queued=1 irq=[01] target=[0-9a-f]{8} lr=80519[0-4][0-9a-f]{3}$'

def derive(source: str) -> str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V147 inherited native test anchor differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V147_SC_IPC_NEXT verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
