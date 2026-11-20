#!/usr/bin/env python3
"""V173 prove 16 owner-original post-Y1-ACK guest calls without fake ACK."""
import argparse
from pathlib import Path
from derive_v172_sc_y1_ack_runner import derive as previous

OLD='python3 "$here/derive_v172_sc_y1_ack_harness.py"'
NEW='python3 "$here/derive_v173_sc_after_y1_ack_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V172_SC_Y1_ACK verified=1'"
PATTERN=r'^V173_SC_AFTER_Y1_ACK y1clear=[01] flag=[01] wire=[01] reply=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] status=[0-9]{1,3} read=[01] write=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V173_SC_AFTER_Y1_ACK y1clear=1 flag=[01] wire=[01] reply=[01] guest=1 caller=1 coherent=1 mapped=1 status=[0-9]{1,3} read=[01] write=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V173 native original previous ACK runner differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V173_SC_AFTER_Y1_ACK verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
