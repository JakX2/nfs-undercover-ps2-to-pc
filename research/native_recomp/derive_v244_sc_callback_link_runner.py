#!/usr/bin/env python3
"""V244 owner-native first callback's original linked call and stack ABI."""
import argparse
from pathlib import Path
from derive_v242_sc_callback_call_route_runner import derive as previous

OLD='python3 "$here/derive_v242_sc_callback_call_route_harness.py"'
NEW='python3 "$here/derive_v244_sc_callback_link_harness.py"'
DONE="echo 'V242_SC_CALLBACK_CALL_ROUTE verified=1'"
NEST=r'^V244_CB_NEST registered=[01] abi=[01] mapped=[01] text=[01] isfs=[01] nand=[01] null=[01]$'
FRAME=r'^V244_FRAME mapped=[01] frame32=[01] frame48=[01] other=[01] outer_lr=[01] nested_lr=[01] text_lr=[01]$'
PATTERN=r'^V244_LINK cb=[01] save=[01] registered=[01] abi=[01] userdata=[01] frame32=[01] frame48=[01] outer_lr=[01] nested_lr=[01] isfs_entry=[0-9]{1,2} nested_text=[01]$'
PASS=r'^V244_LINK cb=1 save=1 registered=1 abi=1 userdata=1 frame32=[01] frame48=[01] outer_lr=[01] nested_lr=[01] isfs_entry=[0-9]{1,2} nested_text=[01]$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V244 prior native first callback route changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V244 prior native failure hook changed")
    for pattern in (NEST,FRAME,PATTERN):
        s=s.replace(fail,'  grep -E "'+pattern+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{NEST}' "$log" | sort -u
grep -E '{FRAME}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V244_SC_CALLBACK_LINK verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
