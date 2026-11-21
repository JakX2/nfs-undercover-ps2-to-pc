#!/usr/bin/env python3
"""V223 original third negative Y1 reply-handler first IPC read runner."""
import argparse
from pathlib import Path
from derive_v222_sc_y1_ipc_next_runner import derive as previous
OLD='python3 "$here/derive_v222_sc_y1_ipc_next_harness.py"'
NEW='python3 "$here/derive_v223_sc_y1_reply_read_harness.py"'
DONE="echo 'V222_SC_Y1_IPC_NEXT verified=1'"
PATTERN=r'^V223_NEG_REPLY_READ irq=[01] wire=[01] caller=[01] guest=[01] masked=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V223_NEG_REPLY_READ irq=1 wire=1 caller=1 guest=1 masked=1 sc=1 pc=8051905c lr=805190e8$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V223 inherited V222 native runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V223 native failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V223_SC_Y1_REPLY_READ verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
