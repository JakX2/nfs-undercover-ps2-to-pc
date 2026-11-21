#!/usr/bin/env python3
"""V236 classify real original IOS_OpenAsync caller sequence and request."""
import argparse
from pathlib import Path
from derive_v235_sc_isfs_helper_abi_runner import derive as previous
OLD='python3 "$here/derive_v235_sc_isfs_helper_abi_harness.py"'
NEW='python3 "$here/derive_v236_sc_second_ios_callers_harness.py"'
DONE="echo 'V235_SC_ISFS_HELPER_ABI verified=1'"
ENTRY=r'^V236_IOS seq=[1-8] after_first=[01] from_isfs=[01] lr_isfs=[01] lr_text=[01] path=[01] sysconf=[01] modevalid=[01] mode_mem2=[01] cb=[01] lr=[0-9a-f]{8}$'
PATTERN=r'^V236_SUBMIT entries=[1-8] early=[0-8] late=[0-8] isfs=[0-8] after_first=[01] from_isfs=[01] pathvalid=[01] modevalid=[01] same_path=[01] same_mode=[01] original_caller=[01] lr=[0-9a-f]{8}$'
PASS=r'^V236_SUBMIT entries=[1-8] early=[1-8] late=[1-8] isfs=[1-8] after_first=1 from_isfs=[01] pathvalid=[01] modevalid=[01] same_path=1 same_mode=1 original_caller=1 lr=[0-9a-f]{8}$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V236 previous verified V235 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V236 inherited native failure exit changed")
    for pattern in (ENTRY,PATTERN):
        s=s.replace(fail,'  grep -E "'+pattern+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{ENTRY}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V236_SC_SECOND_IOS_CALLERS verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
