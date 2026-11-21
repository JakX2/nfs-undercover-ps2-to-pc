#!/usr/bin/env python3
"""V195 verified second IOS Y2 external IRQ hardware entry."""
import argparse
from pathlib import Path
from derive_v194_osrestore_next_runner import derive as previous

OLD='python3 "$here/derive_v194_osrestore_next_harness.py"'
NEW='python3 "$here/derive_v195_sc_y2_irq_entry_harness.py"'
DONE="echo 'V194_RESTORE_NEXT verified=1'"
PATTERN=r'^V195_SC_Y2_VECTOR pending=[01] safe=[01] entered=[01] saved=[01] regs=[01] mail=[01] masked=[01] resume=[0-9a-f]{8} pc=[0-9a-f]{8}$'
PASS=r'^V195_SC_Y2_VECTOR pending=1 safe=1 entered=1 saved=1 regs=1 mail=1 masked=1 resume=8052f830 pc=80000500$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V195 native runner inherited gates changed")
    s=s.replace(OLD,NEW,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V195_SC_Y2_VECTOR verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
