#!/usr/bin/env python3
"""V235 verify original upstream ISFS preserved mode register at four calls."""
import argparse
from pathlib import Path
from derive_v234_sc_isfs_origin_runner import derive as previous
OLD='python3 "$here/derive_v234_sc_isfs_origin_harness.py"'
NEW='python3 "$here/derive_v235_sc_isfs_helper_abi_harness.py"'
DONE="echo 'V234_SC_ISFS_ORIGIN verified=1'"
STAGE=r'^V235_HELPER stage=[1-4] r27valid=[01] r27source=[01] mode_arg=[01] arg_eq_r27=[01] buf_eq_r30=[01]$'
PATTERN=r'^V235_SUMMARY stage=([0-9]|1[0-5]) valid=([0-9]|1[0-5]) source=([0-9]|1[0-5]) ios_modevalid=[01] ios_eq_r27=[01] ios_bufsame=[01] isfs=[01] ios=[01]$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V235 inherited owner-verified V234 source runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V235 native failure exit anchor changed")
    for pattern in (STAGE,PATTERN):
        s=s.replace(fail,'  grep -E "'+pattern+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{STAGE}' "$log" | sort -u || true
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PATTERN}' "$log")" -eq 16
echo 'V235_SC_ISFS_HELPER_ABI verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
