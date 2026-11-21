#!/usr/bin/env python3
"""V232 genuine indirect ISFS callback next PowerPC call with NAND root."""
import argparse
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v231_sc_y1_isfs_callback_runner import derive as previous

OLD='python3 "$here/derive_v231_sc_y1_isfs_callback_harness.py"'
NEW='python3 "$here/derive_v232_sc_isfs_callback_next_harness.py"'
OLD_GENERATOR='python3 "$here/derive_v225_isfs_callback_generator.py" "$here/generate_start_to_ipc_ack_v77.cpp" "$work/generator.cpp"'
NEW_GENERATOR='python3 "$here/derive_v232_nand_callback_generator.py" "$here/generate_start_to_ipc_ack_v77.cpp" "$work/generator.cpp"'
AFTER="for unit in harness generated loader; do"
DONE="echo 'V231_SC_Y1_ISFS_CALLBACK verified=1'"
PATTERN=r'^V232_ISFS_NEXT clear=[01] wire=[01] guest=[01] sc=[01] mapped=[01] selected=[01] nested=[01] result=[01] userdata=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V232_ISFS_NEXT clear=1 wire=1 guest=1 sc=1 mapped=[01] selected=[01] nested=[01] result=[01] userdata=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    for marker in (OLD,OLD_GENERATOR,AFTER,DONE):
        if s.count(marker)!=1:
            raise ValueError("V232 inherited native generator/callback seam changed: "+marker[:46])
    s=s.replace(OLD,NEW,1).replace(OLD_GENERATOR,NEW_GENERATOR,1)
    s=s.replace(AFTER,"""grep -Fx 'V232_CB_ANALYZER rooted=1 analyzed=1' "$work/generation.log" >/dev/null || {
  echo 'V232_NAND_CALLBACK_ROOT verified=0'
  exit 1
}
echo 'V232_NAND_CALLBACK_ROOT verified=1'
"""+AFTER,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V232 owner-original failure hook changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V232_SC_ISFS_CALLBACK_NEXT verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
