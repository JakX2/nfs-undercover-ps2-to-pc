#!/usr/bin/env python3
"""V241 native first ISFS callback entry observation runner."""
import argparse
from pathlib import Path
from derive_v240_sc_first_callback_abi_runner import derive as previous
OLD='python3 "$here/derive_v240_sc_first_callback_abi_harness.py"'
NEW='python3 "$here/derive_v241_sc_first_callback_dispatch_harness.py"'
DONE="echo 'V240_SC_FIRST_CALLBACK verified=1'"
ENTRY=r'^V241_CB_ENTRY seq=[1-8] lr=[01] target=[01] abi=[01] ctr=[01]$'
PATTERN=r'^V241_DISPATCH cb_count=[0-8] traced=[01] registered=[01] trace_enabled=[01] lr_ok=[01] target_ok=[01] abi_ok=[01] ctr_ok=[01] second_invalid=[01] first_reply=[01]$'
PASS=r'^V241_DISPATCH cb_count=[0-8] traced=[01] registered=1 trace_enabled=1 lr_ok=[01] target_ok=[01] abi_ok=[01] ctr_ok=[01] second_invalid=1 first_reply=1$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V241 predecessor owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V241 native failure hook changed")
    for pat in (ENTRY,PATTERN):
        s=s.replace(fail,'  grep -E "'+pat+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{ENTRY}' "$log" | sort -u || true
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V241_SC_FIRST_CALLBACK_DISPATCH verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
