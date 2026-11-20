#!/usr/bin/env python3
"""V152 require sixteen owner-original SC handler post-ACK helper continuations."""
import argparse
from pathlib import Path
from derive_v151_sc_post_flag_runner import derive as previous

OLD='python3 "$here/derive_v151_sc_post_flag_harness.py"'
NEW='python3 "$here/derive_v152_sc_post_helper_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V151_SC_AFTER_FLAG verified=1'"
PATTERN=r'^V152_SC_POST_HELPER clean=[01] idle=[01] queued=[01] guest=[01] text=[01] target=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V152_SC_POST_HELPER clean=1 idle=1 queued=1 guest=1 text=1 target=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V152 inherited owner-native verification gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V152_SC_POST_HELPER verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
