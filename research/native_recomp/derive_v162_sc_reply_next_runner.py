#!/usr/bin/env python3
"""V162 sixteen private-original second SC dispatcher next-call trials."""
import argparse
from pathlib import Path
from derive_v161_sc_y1_dispatch_runner import derive as previous

OLD='python3 "$here/derive_v161_sc_y1_dispatch_harness.py"'
NEW='python3 "$here/derive_v162_sc_reply_next_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V161_SC_Y1_DISPATCH verified=1'"
PATTERN=r'^V162_SC_REPLY_NEXT irq=[01] reply=[01] guest=[01] masked=[01] caller=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V162_SC_REPLY_NEXT irq=1 reply=1 guest=1 masked=1 caller=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V162 original-native runner inherited assertion gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V162_SC_REPLY_NEXT verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
