#!/usr/bin/env python3
"""V237 original ISFS prologue vs twice-executed IOS callsite."""
import argparse
from pathlib import Path
from derive_v236_sc_second_ios_callers_runner import derive as previous
OLD='python3 "$here/derive_v236_sc_second_ios_callers_harness.py"'
NEW='python3 "$here/derive_v237_sc_isfs_reentry_harness.py"'
DONE="echo 'V236_SC_SECOND_IOS_CALLERS verified=1'"
SECOND=r'^V237_SECOND stack=[01] saved_lr=[01] r27valid=[01] r27source=[01] arg_r27=[01] path_r30=[01] same_r30=[01]$'
PATTERN=r'^V237_CHAIN isfs=[0-8] save=[0-8] strn=[0-8] alloc=[0-8] copy=[0-8] ios=[0-8] stack=[01] saved_lr=[01] r27valid=[01] r27source=[01] arg_r27=[01] path_r30=[01]$'
PASS=r'^V237_CHAIN isfs=[1-8] save=[1-8] strn=[1-8] alloc=[1-8] copy=[1-8] ios=[2-8] stack=[01] saved_lr=[01] r27valid=[01] r27source=[01] arg_r27=[01] path_r30=[01]$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V237 inherited owner-original V236 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V237 inherited owner-native exit changed")
    for pattern in (SECOND,PATTERN):
        s=s.replace(fail,'  grep -E "'+pattern+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{SECOND}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V237_SC_ISFS_REENTRY verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
