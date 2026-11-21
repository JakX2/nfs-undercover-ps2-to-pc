#!/usr/bin/env python3
"""V206 original second IOS Y2 post-Hollywood-ACK native successor."""
import argparse
from pathlib import Path
from derive_v205_sc_y2_flag_runner import derive as previous

OLD='python3 "$here/derive_v205_sc_y2_flag_harness.py"'
NEW='python3 "$here/derive_v206_sc_y2_post_flag_harness.py"'
DONE="echo 'V205_SC_Y2_FLAG verified=1'"
PATTERN=r'^V206_Y2_POST ack=[01] irq_down=[01] queued=[01] open=[01] guest=[01] masked=[01] coherent=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V206_Y2_POST ack=1 irq_down=1 queued=1 open=1 guest=1 masked=1 coherent=1 sc=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V206 inherited V205 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V206 native failure-exit anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V206_SC_Y2_POST_FLAG verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
