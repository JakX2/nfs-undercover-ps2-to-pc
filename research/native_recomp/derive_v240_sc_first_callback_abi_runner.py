#!/usr/bin/env python3
"""V240 first IOS callback register/CTR source, source-only native runner."""
import argparse
from pathlib import Path
from derive_v239_sc_isfs_caller_return_runner import derive as previous
OLD='python3 "$here/derive_v239_sc_isfs_caller_return_harness.py"'
NEW='python3 "$here/derive_v240_sc_first_callback_abi_harness.py"'
DONE="echo 'V239_SC_ISFS_CALLER verified=1'"
ENTRY=r'^V240_FIRST_CB first=[01] reply=[01] cb_isfsfunc=[01] cb_isfsopen=[01] cb_text=[01] r3_reply=[01] r4_userdata=[01] ctr_cb=[01] ctr_isfsopen=[01] ipc_return=[01]$'
PATTERN=r'^V240_CB_CHAIN seen=[01] first=[01] reply=[01] cb_isfsfunc=[01] cb_isfsopen=[01] cb_text=[01] r3_reply=[01] r4_userdata=[01] ctr_cb=[01] ctr_isfsopen=[01] ipc_return=[01]$'
PASS=r'^V240_CB_CHAIN seen=1 first=1 reply=[01] cb_isfsfunc=[01] cb_isfsopen=[01] cb_text=[01] r3_reply=[01] r4_userdata=[01] ctr_cb=[01] ctr_isfsopen=[01] ipc_return=1$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V240 inherited V239 owner original runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V240 original-native failure marker changed")
    for pat in (ENTRY,PATTERN):
        s=s.replace(fail,'  grep -E "'+pat+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{ENTRY}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V240_SC_FIRST_CALLBACK verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
