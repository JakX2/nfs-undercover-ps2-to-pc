#!/usr/bin/env python3
"""V153 prove sixteen owner-native SC post-IRQ native IOS reply publications."""
import argparse
from pathlib import Path
from derive_v152_sc_post_helper_runner import derive as previous

OLD='python3 "$here/derive_v152_sc_post_helper_harness.py"'
NEW='python3 "$here/derive_v153_sc_reply_handoff_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V152_SC_POST_HELPER verified=1'"
PATTERN=r'^V153_SC_REPLY route=[01] cleared=[01] service=[01] wire=[01] fd=[01] signal=[01]$'
PRE_PATTERN=r'^V153_SC_PRE route=[01] present=[01] aligned=[01] mapped=[01] open=[01] prior=[01] same=[01] clear=[01] queued=[01] masked=[01]$'
PASS="V153_SC_REPLY route=1 cleared=1 service=1 wire=1 fd=1 signal=1"

def derive(source: str) -> str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V153 inherited source gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+PRE_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -Fx '{PASS}' "$log" | sort -u
test "$(grep -Fxc '{PASS}' "$log")" -eq 16
grep -Fx 'V153_SC_REPLY_STATE bridge=1 wire=1 mail=1 drained=1 irq=1' "$log" | sort -u
echo 'V153_SC_REPLY verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
