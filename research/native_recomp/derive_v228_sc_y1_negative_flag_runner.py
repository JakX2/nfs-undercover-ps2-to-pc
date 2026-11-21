#!/usr/bin/env python3
"""V228 third negative Y1 Hollywood W1C and cache-helper owner runner."""
import argparse
from pathlib import Path
from derive_v227_sc_y1_negative_ack_runner import derive as previous
OLD='python3 "$here/derive_v227_sc_y1_negative_ack_harness.py"'
NEW='python3 "$here/derive_v228_sc_y1_negative_flag_harness.py"'
DONE="echo 'V227_SC_Y1_NEGATIVE_ACK verified=1'"
PATTERN=r'^V228_NEG_FLAG y1=[01] w1c=[01] flag=[01] irq_down=[01] reply=[01] guest=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V228_NEG_FLAG y1=1 w1c=1 flag=1 irq_down=1 reply=1 guest=1 sc=1 pc=80522294 lr=80519124$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V228 inherited original V227 native owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V228 native owner failure hook changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V228_SC_Y1_NEGATIVE_FLAG verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
