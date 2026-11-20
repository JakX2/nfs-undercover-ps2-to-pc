#!/usr/bin/env python3
"""V166 require original second SC nested interrupt restore successor, 16 times."""
import argparse
from pathlib import Path
from derive_v165_sc_y1_post_osdi_runner import derive as previous

OLD='python3 "$here/derive_v165_sc_y1_post_osdi_harness.py"'
NEW='python3 "$here/derive_v166_sc_post_restore_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V165_SC_POST_OSDI verified=1'"
PATTERN=r'^V166_SC_POST_RESTORE irq=[01] reply=[01] guest=[01] call=[01] coherent=[01] ee=[01] ready=[01] ipc=[01] helper=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V166_SC_POST_RESTORE irq=1 reply=1 guest=1 call=1 coherent=1 ee=[01] ready=[01] ipc=[01] helper=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V166 native runner inherited original V165 gate changed")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V166_SC_POST_RESTORE verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
