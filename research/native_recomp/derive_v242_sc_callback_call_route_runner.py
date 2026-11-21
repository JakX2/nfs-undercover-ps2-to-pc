#!/usr/bin/env python3
"""V242 original callback-to-second-ISFS call route, owner-native runner."""
import argparse
from pathlib import Path
from derive_v241_sc_first_callback_dispatch_runner import derive as previous
OLD='python3 "$here/derive_v241_sc_first_callback_dispatch_harness.py"'
NEW='python3 "$here/derive_v242_sc_callback_call_route_harness.py"'
DONE="echo 'V241_SC_FIRST_CALLBACK_DISPATCH verified=1'"
TRACE=r'^V242_TRACE seq=([1-9]|1[0-9]|2[0-4]) cb=[01] isfs=[01] ipc=[01] lr_text=[01] handler_lr=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{1,8}$'
PATTERN=r'^V242_ROUTE count=([1-9]|1[0-9]|2[0-4]) cb=[0-9]{1,2} isfs_entry=[0-9]{1,2} handler_lr=[0-9]{1,2} captured=[01] second=[01] last_pc=[0-9a-f]{8} last_lr=[0-9a-f]{1,8}$'
PASS=r'^V242_ROUTE count=([1-9]|1[0-9]|2[0-4]) cb=[0-9]{1,2} isfs_entry=[0-9]{1,2} handler_lr=[0-9]{1,2} captured=1 second=1 last_pc=[0-9a-f]{8} last_lr=[0-9a-f]{1,8}$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V242 inherited owner-native V241 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V242 original failure exit changed")
    for pat in (TRACE,PATTERN):
        s=s.replace(fail,'  grep -E "'+pat+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{TRACE}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V242_SC_CALLBACK_CALL_ROUTE verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
