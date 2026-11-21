#!/usr/bin/env python3
"""V234 original upstream ISFS mode ABI before the proven IOS mismatch."""
import argparse
from pathlib import Path
from derive_v233_sc_second_open_abi_runner import derive as previous
OLD='python3 "$here/derive_v233_sc_second_open_abi_harness.py"'
NEW='python3 "$here/derive_v234_sc_isfs_origin_harness.py"'
DONE="echo 'V233_SC_SECOND_OPEN_ABI verified=1'"
ISFS=r'^V234_ISFS seq=[1-8] path=[01] sysconf=[01] modevalid=[01] nand_cb=[01] guest=[01]$'
ROUTE=r'^V234_ROUTE isfs=[01] mode_same=[01] isfs_modevalid=[01] ios_modevalid=[01] ios_cb=[01]$'
PATTERN=r'^V234_SOURCE isfs=[01] count=[0-8] ios=[01] isfs_valid=[01] ios_valid=[01] mode_isfs=[01] mode_ios=[01] nand_cb=[01]$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V234 inherited verified V233 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V234 owner failure exit changed")
    for pattern in (ISFS,ROUTE,PATTERN):
        s=s.replace(fail,'  grep -E "'+pattern+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{ISFS}' "$log" | sort -u || true
grep -E '{ROUTE}' "$log" | sort -u || true
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PATTERN}' "$log")" -eq 16
echo 'V234_SC_ISFS_ORIGIN verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
