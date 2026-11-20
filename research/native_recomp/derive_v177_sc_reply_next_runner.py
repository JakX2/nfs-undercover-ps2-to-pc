#!/usr/bin/env python3
"""V177 sixteen owner-original SYSCONF reply callee next-function trials."""
import argparse
from pathlib import Path
from derive_v176_sc_reply_next_runner import derive as previous

OLD='python3 "$here/derive_v176_sc_reply_next_harness.py"'
NEW='python3 "$here/derive_v177_sc_reply_next_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V176_SC_REPLY_NEXT verified=1'"
PATTERN=r'^V177_SC_REPLY_NEXT clean=[01] wire=[01] queue=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] before=[0-9]{1,3} status=[0-9]{1,3} changed=[01] ipc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V177_SC_REPLY_NEXT clean=[01] wire=[01] queue=[01] guest=1 caller=1 coherent=1 mapped=1 before=1 status=[0-9]{1,3} changed=[01] ipc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V177 private original runner inherited source gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V177_SC_REPLY_NEXT verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
