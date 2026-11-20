#!/usr/bin/env python3
"""V168 require sixteen original Wii Y1 register-read guest successor trials."""
import argparse
from pathlib import Path
from derive_v167_sc_reply_leaf_runner import derive as previous

OLD='python3 "$here/derive_v167_sc_reply_leaf_harness.py"'
NEW='python3 "$here/derive_v168_sc_reply_read_next_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V167_SC_REPLY_LEAF verified=1'"
PATTERN=r'^V168_SC_REPLY_NEXT y1=[01] reply=[01] guest=[01] masked=[01] caller=[01] read=[01] other=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V168_SC_REPLY_NEXT y1=1 reply=1 guest=1 masked=1 caller=1 read=[01] other=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V168 native runner inherited original V167 gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V168_SC_REPLY_NEXT verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
