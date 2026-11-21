#!/usr/bin/env python3
"""V239 original second ISFS saved-caller return provenance runner."""
import argparse
from pathlib import Path
from derive_v238_sc_isfs_prologue_source_runner import derive as previous
OLD='python3 "$here/derive_v238_sc_isfs_prologue_source_harness.py"'
NEW='python3 "$here/derive_v239_sc_isfs_caller_return_harness.py"'
DONE="echo 'V238_SC_ISFS_PROLOGUE verified=1'"
ENTRY=r'^V239_ISFS_RETURN text=[01] ipc=[01] isfs=[01] nand_region=[01] os=[01] same_first=[01] modevalid=[01] pathvalid=[01] ret=[0-9a-f]{1,8}$'
PATTERN=r'^V239_ISFS_CHAIN ready=[01] text=[01] same_first=[01] invalid=[01] ios_invalid=[01] same_ios_mode=[01]$'
PASS=r'^V239_ISFS_CHAIN ready=1 text=1 same_first=0 invalid=1 ios_invalid=1 same_ios_mode=1$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V239 authenticated owner original V238 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V239 native failure anchor changed")
    for pat in (ENTRY,PATTERN):
        s=s.replace(fail,'  grep -E "'+pat+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{ENTRY}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V239_SC_ISFS_CALLER verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
