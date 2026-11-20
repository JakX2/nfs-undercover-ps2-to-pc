#!/usr/bin/env python3
"""V148 native owner-original SC IPC distinct-leaf stop, after V147 regressions."""
import argparse
from pathlib import Path
from derive_v147_sc_ipc_next_runner import derive as previous

OLD='python3 "$here/derive_v147_sc_ipc_next_harness.py"'
NEW='python3 "$here/derive_v148_sc_ipc_distinct_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V147_SC_IPC_NEXT verified=1'"
PATTERN=r'^V148_SC_IPC_DISTINCT first=[01] caller=[01] advanced=[01] masked=[01] queued=[01] irq=[01] reads=[0-9]{1,2} target=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V148_SC_IPC_DISTINCT first=1 caller=1 advanced=1 masked=1 queued=1 irq=[01] reads=[0-9]{1,2} target=[0-9a-f]{8} lr=80519[34][0-9a-f]{2}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V148 native source gate differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
      '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
      '  grep -E "^V148_SC_IPC_READ_LIMIT count=[0-9]{1,2}$" "$work/private-native.log" | sort -u || true\n'
      +FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V148_SC_IPC_DISTINCT verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
