#!/usr/bin/env python3
"""V193 original PPC OSDisableInterrupts successor after verified V192."""
import argparse
from pathlib import Path
from derive_v192_osinit_retry_next_runner import derive as previous

OLD='python3 "$here/derive_v192_osinit_retry_next_harness.py"'
NEW='python3 "$here/derive_v193_osdi_next_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V192_OSINIT_NEXT verified=1'"
PATTERN=r'^V193_OSDI_NEXT y2=[01] flag=[01] queue=[01] guest=[01] coherent=[01] mapped=[01] caller=[01] sc=[0-9]{1,3} ee=[01] ready=[01] r3=[0-9]{1,10} eq=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V193_OSDI_NEXT y2=[01] flag=[01] queue=[01] guest=1 coherent=1 mapped=1 caller=1 sc=[0-9]{1,3} ee=[01] ready=[01] r3=[0-9]{1,10} eq=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
STATE=r'^V193_OSDI_STATE guest=[01] irq=[01] sc=[01] queue=[01]$'
PASS_STATE=r'^V193_OSDI_STATE guest=1 irq=1 sc=1 queue=1$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V193 owner native runner inherited V192 anchors changed")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+STATE+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    success='  echo "V186_NATIVE_SUCCESS pre=$v186_pre ack=$v186_ack state=$v186_state previous=$v186_v185"'
    if s.count(success)!=1:
        raise ValueError("V193 authenticated native-success event changed")
    diagnostic = """  v193_next=$(grep -Ec '^V193_OSDI_NEXT ' "$work/private-native.log" || true)
  v193_state=$(grep -Ec '^V193_OSDI_STATE ' "$work/private-native.log" || true)
  [[ "$v193_next" =~ ^[0-9]{1,2}$ && "$v193_state" =~ ^[0-9]{1,2}$ ]] || exit 1
  echo "V193_GUEST_PROBE next=$v193_next state=$v193_state"
""" + (
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+STATE+'" "$work/private-native.log" | sort -u || true\n'
    )
    s=s.replace(success,success+"\n"+diagnostic,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -E '{PASS_STATE}' "$log" | sort -u
test "$(grep -Ec '{PASS_STATE}' "$log")" -eq 16
echo 'V193_OSDI_NEXT verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
