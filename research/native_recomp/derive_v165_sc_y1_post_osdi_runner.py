#!/usr/bin/env python3
"""V165 sixteen owner-original SC Y1 nested OSDI continuation trials."""
import argparse
from pathlib import Path
from derive_v164_sc_y1_nested_helper_runner import derive as previous

OLD='python3 "$here/derive_v164_sc_y1_nested_helper_harness.py"'
NEW='python3 "$here/derive_v165_sc_y1_post_osdi_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V164_SC_Y1_NESTED verified=1'"
PATTERN=r'^V165_SC_POST_OSDI irq=[01] reply=[01] masked=[01] guest=[01] caller=[01] ipc=[01] helper=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V165_SC_POST_OSDI irq=1 reply=1 masked=1 guest=1 caller=1 ipc=[01] helper=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V165 private-original prior runner check differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V165_SC_POST_OSDI verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
