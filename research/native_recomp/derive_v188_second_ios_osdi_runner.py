#!/usr/bin/env python3
"""V188 execute original Wii OSDI after second authentic IOS ACK."""
import argparse
from pathlib import Path
from derive_v187_second_ios_next_runner import derive as previous

OLD='python3 "$here/derive_v187_second_ios_next_harness.py"'
NEW='python3 "$here/derive_v188_second_ios_osdi_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V187_SC_NEXT verified=1'"
PATTERN=r'^V188_SC_NEXT y2=[01] flag=[01] queue=[01] request=[01] guest=[01] caller=[01] masked=[01] coherent=[01] mapped=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V188_SC_NEXT y2=[01] flag=[01] queue=1 request=1 guest=1 caller=1 masked=1 coherent=1 mapped=1 sc=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
STATE=r'^V188_SC_STATE guest=[01] queue=[01] irq=[01] masked=[01] sc=[01]$'
PASS_STATE=r'^V188_SC_STATE guest=1 queue=1 irq=1 masked=1 sc=1$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V188 original-free owner runner precursor differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+STATE+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -Fx 'V188_SC_STATE guest=1 queue=1 irq=1 masked=1 sc=1' "$log" | sort -u
test "$(grep -Ec '{PASS_STATE}' "$log")" -eq 16
echo 'V188_SC_OSDI verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
