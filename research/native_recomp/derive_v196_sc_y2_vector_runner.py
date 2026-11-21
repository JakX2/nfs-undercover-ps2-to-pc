#!/usr/bin/env python3
"""V196 original Wii PowerPC handler entry for the second Y2 interrupt."""
import argparse
from pathlib import Path
from derive_v195_sc_y2_irq_entry_runner import derive as previous

OLD='python3 "$here/derive_v195_sc_y2_irq_entry_harness.py"'
NEW='python3 "$here/derive_v196_sc_y2_vector_harness.py"'
DONE="echo 'V195_SC_Y2_VECTOR verified=1'"
PATTERN=r'^V196_Y2_VECTOR vector=[01] handler=[01] saved=[01] pending=[01] progressed=[01] resume=[0-9a-f]{8} pc=[0-9a-f]{8}$'
PASS=r'^V196_Y2_VECTOR vector=1 handler=1 saved=1 pending=1 progressed=1 resume=8052f830 pc=80526ce0$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V196 owner original runner inherited V195 markers changed")
    s=s.replace(OLD,NEW,1)
    success='  echo "V186_NATIVE_SUCCESS pre=$v186_pre ack=$v186_ack state=$v186_state previous=$v186_v185"'
    if s.count(success)!=1:
        raise ValueError("V196 native owner trial success anchor changed")
    diag=(
        '  v196_count=$(grep -Ec "^V196_Y2_VECTOR " "$work/private-native.log" || true)\n'
        '  [[ "$v196_count" =~ ^[0-9]{1,2}$ ]] || exit 1\n'
        '  echo "V196_ENTRY_COUNT lines=$v196_count"\n'
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
    )
    s=s.replace(success,success+"\n"+diag,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V196_SC_Y2_VECTOR verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
