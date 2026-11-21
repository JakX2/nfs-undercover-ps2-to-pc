#!/usr/bin/env python3
"""V246 original NAND second callback owner-native runner."""
import argparse
from pathlib import Path
from derive_v244_sc_callback_link_runner import derive as previous

OLD='python3 "$here/derive_v244_sc_callback_link_harness.py"'
NEW='python3 "$here/derive_v246_sc_nand_second_callback_harness.py"'
DONE="echo 'V244_SC_CALLBACK_LINK verified=1'"
TARGET=r'^V246_SECOND_TARGET outer=[01] nested=[01] text=[01] isfs=[01] nand=[01] cb=[01] null=[01]$'
CTR=r'^V246_SECOND_CTR known=[01] match=[01] isfs=[01] nand=[01] cb=[01] text=[01] outer_lr=[01]$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V246 original V244 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V246 original owner failure hook changed")
    for pattern in (TARGET,CTR):
        s=s.replace(fail,'  grep -E "'+pattern+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
test "$(grep -Ec '{TARGET}' "$log")" -eq 16
test "$(grep -Ec '{CTR}' "$log")" -eq 16
grep -E '{TARGET}' "$log" | sort -u
grep -E '{CTR}' "$log" | sort -u
echo 'V246_SC_NAND_SECOND_CALLBACK verified=1'
""",1)

if __name__=="__main__":
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("source",type=Path)
    args.add_argument("output",type=Path)
    a=args.parse_args()
    with a.output.open("x",encoding="utf-8") as dst:
        dst.write(derive(a.source.read_text(encoding="utf-8")))
