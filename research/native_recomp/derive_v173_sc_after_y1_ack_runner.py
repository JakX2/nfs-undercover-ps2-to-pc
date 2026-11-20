#!/usr/bin/env python3
"""V173 prove sixteen original Y1/flag acknowledgments and genuine next calls."""
import argparse
from pathlib import Path
from derive_v172_sc_y1_ack_runner import derive as previous

OLD='python3 "$here/derive_v172_sc_y1_ack_harness.py"'
NEW='python3 "$here/derive_v173_sc_after_y1_ack_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V172_SC_Y1_ACK verified=1'"
PATTERN=r'^V173_SC_AFTER_Y1_ACK y1clear=[01] flag=[01] wire=[01] reply=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] status=[0-9]{1,3} read=[01] write=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V173_SC_AFTER_Y1_ACK y1clear=1 flag=0 wire=1 reply=1 guest=1 caller=1 coherent=1 mapped=1 status=[0-9]{1,3} read=[01] write=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
HW_PATTERN=r'^V173_SC_HW_FLAG_W1C guest=1 count=[0-9]{1,3} cleared=[01] irq_down=[01]$'
HW_PASS='V173_SC_HW_FLAG_W1C guest=1 count=1 cleared=1 irq_down=1'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V173 native original previous ACK runner differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
       '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
       +'  grep -E "'+HW_PATTERN+'" "$work/private-native.log" | sort -u || true\n'
       +FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -Fx '{HW_PASS}' "$log" | sort -u
test "$(grep -Fxc '{HW_PASS}' "$log")" -eq 16
echo 'V173_SC_AFTER_Y1_ACK verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
