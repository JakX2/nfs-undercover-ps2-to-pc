#!/usr/bin/env python3
"""V172 require 16 real SC Y1 reply PPCCTRL guest W1C write trials."""
import argparse
from pathlib import Path
from derive_v171_sc_reply_distinct_runner import derive as previous

OLD='python3 "$here/derive_v171_sc_reply_distinct_harness.py"'
NEW='python3 "$here/derive_v172_sc_reply_y1_ack_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V171_SC_DISTINCT verified=1'"
PATTERN=r'^V172_SC_REPLY_Y1_ACK write=[01] cleared=[01] latched=[01] guest=[01] reply=[01] mapped=[01] status=[0-9]{1,3}$'
PASS=r'^V172_SC_REPLY_Y1_ACK write=1 cleared=1 latched=1 guest=1 reply=1 mapped=1 status=[0-9]{1,3}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V172 prior original guest runner gates changed")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V172_SC_REPLY_Y1_ACK verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
