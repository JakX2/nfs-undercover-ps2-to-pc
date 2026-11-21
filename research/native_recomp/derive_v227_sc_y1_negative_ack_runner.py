#!/usr/bin/env python3
"""V227 native Wii third Y1 negative reply PPCCTRL write-one-to-clear."""
import argparse
from pathlib import Path
from derive_v226_sc_y1_reply_successor_runner import derive as previous
OLD='python3 "$here/derive_v226_sc_y1_reply_successor_harness.py"'
NEW='python3 "$here/derive_v227_sc_y1_negative_ack_harness.py"'
DONE="echo 'V226_SC_Y1_REPLY_SUCCESSOR verified=1'"
PATTERN=r'^V227_NEG_Y1_ACK wrote=[01] cleared=[01] flag=[01] irq=[01] wire=[01] guest=[01] advanced=[01] sc=[01]$'
PASS=r'^V227_NEG_Y1_ACK wrote=1 cleared=1 flag=1 irq=1 wire=1 guest=1 advanced=1 sc=1$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V227 authenticated native V226 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V227 original-native failure hook changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V227_SC_Y1_NEGATIVE_ACK verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
