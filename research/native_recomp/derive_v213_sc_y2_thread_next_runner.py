#!/usr/bin/env python3
"""V213 owner-native second-IOS RFI-restored thread next guest call."""
import argparse
from pathlib import Path
from derive_v212_sc_y2_rfi_runner import derive as previous

OLD='python3 "$here/derive_v212_sc_y2_rfi_harness.py"'
NEW='python3 "$here/derive_v213_sc_y2_thread_next_harness.py"'
DONE="echo 'V212_SC_Y2_RFI verified=1'"
PATTERN=r'^V213_Y2_THREAD guest=[01] caller=[01] coherent=[01] mapped=[01] irq_down=[01] queued=[01] open=[01] sc=[0-9]{1,3} ee=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V213_Y2_THREAD guest=1 caller=1 coherent=1 mapped=1 irq_down=1 queued=1 open=1 sc=[0-9]{1,3} ee=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V213 owner-original V212 runner anchor changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V213 owner native failure-exit changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V213_SC_Y2_THREAD_NEXT verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as f:
        f.write(derive(args.source.read_text(encoding="utf-8")))
