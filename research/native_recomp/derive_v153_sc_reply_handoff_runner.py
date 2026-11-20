#!/usr/bin/env python3
"""V153 prove sixteen owner-native SC post-IRQ native IOS reply publications."""
import argparse
from pathlib import Path
from derive_v152_sc_post_helper_runner import derive as previous

OLD='python3 "$here/derive_v152_sc_post_helper_harness.py"'
NEW='python3 "$here/derive_v153_sc_reply_handoff_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V152_SC_POST_HELPER verified=1'"
PATTERN=r'^V153_SC_REPLY bridge=[01] wire=[01] mail=[01] drained=[01] irq=[01]$'
PASS="V153_SC_REPLY bridge=1 wire=1 mail=1 drained=1 irq=1"

def derive(source: str) -> str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V153 inherited source gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -Fx '{PASS}' "$log" | sort -u
test "$(grep -Fxc '{PASS}' "$log")" -eq 16
echo 'V153_SC_REPLY verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
