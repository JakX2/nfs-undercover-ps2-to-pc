#!/usr/bin/env python3
"""V231 original second IOS negative response into actual ISFS callback."""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v230_sc_y1_context_next_runner import derive as previous

OLD='python3 "$here/derive_v230_sc_y1_context_next_harness.py"'
NEW='python3 "$here/derive_v231_sc_y1_isfs_callback_harness.py"'
DONE="echo 'V230_SC_Y1_CONTEXT_NEXT verified=1'"
PATTERN=r'^V231_ISFS_CALLBACK clear=[01] wire=[01] header=[01] selected=[01] same=[01] abi=[01] userdata=[01] guest=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V231_ISFS_CALLBACK clear=1 wire=1 header=1 selected=1 same=1 abi=1 userdata=1 guest=1 sc=1 pc=804f0e04 lr=805192ac$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V231 authenticated original V230 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V231 original native failure hook changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V231_SC_Y1_ISFS_CALLBACK verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
