#!/usr/bin/env python3
"""V232 genuine indirect ISFS callback next PowerPC call with the verified V225 AOT root."""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v231_sc_y1_isfs_callback_runner import derive as previous

OLD='python3 "$here/derive_v231_sc_y1_isfs_callback_harness.py"'
NEW='python3 "$here/derive_v232_sc_isfs_callback_next_harness.py"'
DONE="echo 'V231_SC_Y1_ISFS_CALLBACK verified=1'"
PATTERN=r'^V232_ISFS_NEXT clear=[01] wire=[01] guest=[01] sc=[01] mapped=[01] selected=[01] from_isfs=[01] nested=[01] result=[01] userdata=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V232_ISFS_NEXT clear=1 wire=1 guest=1 sc=1 mapped=[01] selected=[01] from_isfs=[01] nested=[01] result=[01] userdata=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V232 inherited verified V231 guest entry changed")
    # Keep the V225 baseline generator. Adding the NAND callback root
    # changed an earlier native allocator assertion, before V232 was hit.
    # This run identifies the actual callback target first.
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V232 owner-original failure hook changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V232_SC_ISFS_CALLBACK_NEXT verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
