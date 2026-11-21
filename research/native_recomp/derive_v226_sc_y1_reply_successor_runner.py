#!/usr/bin/env python3
"""V226 actual third negative Y1 IpcReplyHandler next translated call."""
import argparse
from pathlib import Path
from derive_v224_sc_y1_reply_second_read_runner import derive as previous

OLD='python3 "$here/derive_v224_sc_y1_reply_second_read_harness.py"'
NEW='python3 "$here/derive_v226_sc_y1_reply_successor_harness.py"'
DONE="echo 'V224_SC_Y1_SECOND_READ verified=1'"
PATTERN=r'^V226_NEG_SUCCESSOR signal=[01] negative=[01] guest=[01] caller=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V226_NEG_SUCCESSOR signal=1 negative=1 guest=1 caller=1 sc=1 pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V226 V224 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V226 original-native failure observer changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V226_SC_Y1_REPLY_SUCCESSOR verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
