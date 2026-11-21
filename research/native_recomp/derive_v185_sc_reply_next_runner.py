#!/usr/bin/env python3
"""V185 verify first authentic PPC function after V184 original IPC read."""
import argparse
from pathlib import Path
from derive_v184_sc_reply_burst_runner import derive as previous

OLD='python3 "$here/derive_v184_sc_reply_burst_harness.py"'
NEW='python3 "$here/derive_v185_sc_reply_next_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V184_SC_BURST verified=1'"
ENTRY=r'^V185_IPC_ENTRY phase=1 request=[01] x1=[01] y1=[01] y2=[01] open=[01] replied=[01] status=[0-9]{1,3}$'
PATTERN=r'^V185_SC_NEXT clean=[01] x1=[01] request=[01] replied=[01] queue=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] before=[0-9]{1,3} status=[0-9]{1,3} changed=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V185_SC_NEXT clean=[01] x1=[01] request=[01] replied=[01] queue=[01] guest=1 caller=1 coherent=1 mapped=1 before=1 status=[0-9]{1,3} changed=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V185 private owner-original runner inherited guards differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+ENTRY+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -E '{ENTRY}' "$log" | sort -u
test "$(grep -Ec '{ENTRY}' "$log")" -eq 16
echo 'V185_SC_NEXT verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
