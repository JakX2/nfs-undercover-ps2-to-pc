#!/usr/bin/env python3
"""V203 original second Y2 IPC repeated reads to distinct helper."""
import argparse
from pathlib import Path
from derive_v202_sc_y2_next_runner import derive as previous

OLD='python3 "$here/derive_v202_sc_y2_next_harness.py"'
NEW='python3 "$here/derive_v203_sc_y2_distinct_harness.py"'
DONE="echo 'V202_SC_Y2_NEXT verified=1'"
PATTERN=r'^V203_Y2_DISTINCT first=[01] caller=[01] progressed=[01] masked=[01] queued=[01] reads=[0-9]{1,2} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V203_Y2_DISTINCT first=1 caller=1 progressed=1 masked=1 queued=1 reads=[0-9]{1,2} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V203 inherited native V202 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V203 native failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V203_SC_Y2_DISTINCT verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
