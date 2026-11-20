#!/usr/bin/env python3
"""V154 original SC scheduler helper successor in sixteen owner-native trials."""
import argparse
from pathlib import Path
from derive_v153_sc_reply_handoff_runner import derive as previous

OLD='python3 "$here/derive_v153_sc_reply_handoff_harness.py"'
NEW='python3 "$here/derive_v154_sc_scheduler_next_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V153_SC_REPLY verified=1'"
PATTERN=r'^V154_SC_SCHED_NEXT signal=[01] reply=[01] guest=[01] target=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V154_SC_SCHED_NEXT signal=1 reply=1 guest=1 target=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V154 SC successor native runner anchors differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V154_SC_SCHED_NEXT verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
