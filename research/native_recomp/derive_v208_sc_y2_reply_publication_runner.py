#!/usr/bin/env python3
"""V208 original second IOS_Open guest-yield reply publication runner."""
import argparse
from pathlib import Path
from derive_v207_sc_y2_helper_next_runner import derive as previous

OLD='python3 "$here/derive_v207_sc_y2_helper_next_harness.py"'
NEW='python3 "$here/derive_v208_sc_y2_reply_publication_harness.py"'
DONE="echo 'V207_SC_Y2_HELPER_NEXT verified=1'"
PATTERN=r'^V208_Y2_REPLY step=[01] wire=[01] opened=[01] signal=[01] drained=[01] cpu=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V208_Y2_REPLY step=1 wire=1 opened=1 signal=1 drained=1 cpu=1 sc=1 pc=80529434 lr=80526cb0$'
KIND=r'^V208_Y2_KIND immediate=[01] event=[01] fs=[01] file=[01] es=[01] negative=[01]$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V208 inherited original V207 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V208 original-native runner failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+KIND+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V208_SC_Y2_REPLY_PUBLICATION verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
