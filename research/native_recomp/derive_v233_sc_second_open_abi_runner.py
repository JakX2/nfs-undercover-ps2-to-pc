#!/usr/bin/env python3
"""V233 upstream Wii original second IOS_Open arguments and wire."""
import argparse
from pathlib import Path
from derive_v214_sc_y2_negative_reply_runner import derive as previous

OLD='python3 "$here/derive_v214_sc_y2_negative_reply_harness.py"'
NEW='python3 "$here/derive_v233_sc_second_open_abi_harness.py"'
DONE="echo 'V214_SC_Y2_NEGATIVE verified=1'"
ABI=r'^V233_ABI layer=(isfs|ios) path=[01] sysconf=[01] modevalid=[01] callback=[01] guest=[01]$'
PATTERN=r'^V233_SUBMIT isfs=[01] ios=[01] isfs_path12=[01] isfs_mode16=[01] ios_path12=[01] ios_mode16=[01] ios_shifted=[01] isfs_cb=[01] ios_cb=[01]$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V233 inherited verified V214 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V233 private diagnostic failure exit changed")
    s=s.replace(fail,'  grep -E "'+ABI+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{ABI}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PATTERN}' "$log")" -eq 16
echo 'V233_SC_SECOND_OPEN_ABI verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
