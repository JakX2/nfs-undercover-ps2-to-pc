#!/usr/bin/env python3
"""V230 original OSClearContext into OSSetCurrentContext owner-native."""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v229_sc_y1_post_cache_runner import derive as previous
OLD='python3 "$here/derive_v229_sc_y1_post_cache_harness.py"'
NEW='python3 "$here/derive_v230_sc_y1_context_next_harness.py"'
DONE="echo 'V229_SC_Y1_POST_CACHE verified=1'"
PATTERN=r'^V230_CONTEXT_NEXT irq_down=[01] wire=[01] guest=[01] context=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V230_CONTEXT_NEXT irq_down=1 wire=1 guest=1 context=1 sc=1 pc=805228cc lr=80519298$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V230 inherited owner V229 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V230 native trial failure hook changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V230_SC_Y1_CONTEXT_NEXT verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
