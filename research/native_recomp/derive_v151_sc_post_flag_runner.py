#!/usr/bin/env python3
"""V151 original SC interrupt post-flag caller checkpoint in sixteen owner trials."""
import argparse
from pathlib import Path
from derive_v150_sc_irq_flag_runner import derive as previous

OLD='python3 "$here/derive_v150_sc_irq_flag_harness.py"'
NEW='python3 "$here/derive_v151_sc_post_flag_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V150_SC_IRQ_CLEAR verified=1'"
PATTERN=r'^V151_SC_AFTER_FLAG cleared=[01] irq_down=[01] queued=[01] masked=[01] progressed=[01] text=[01] target=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V151_SC_AFTER_FLAG cleared=1 irq_down=1 queued=1 masked=1 progressed=1 text=1 target=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V151 owner original source gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V151_SC_AFTER_FLAG verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
