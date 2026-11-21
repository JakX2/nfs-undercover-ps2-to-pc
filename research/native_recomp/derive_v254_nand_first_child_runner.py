#!/usr/bin/env python3
"""V254 run genuine restored NAND PowerPC body to first child call."""
import argparse
from pathlib import Path
from derive_v250_restored_callback_nand_runner import derive as previous

OLD='python3 "$V110_SOURCE_ROOT/derive_v250_restored_callback_nand_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v254_nand_first_child_harness.py"'
DONE="echo 'V250_SC_NAND_BCTRL verified=1'"
PATTERN=r'^V254_NAND_CHILD guest=[01] caller=[01] reply=[01] mapped=[01] frame=[01] coherent=[01] text=[01] low=[01] sc=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V254_NAND_CHILD guest=1 caller=1 reply=1 mapped=1 frame=1 coherent=1 text=[01] low=[01] sc=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
TRIAL=r'^V254_NAND_GUEST callback=1 next=1 memory=1 trial=([1-9]|1[0-6])$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V254 owner-original restored callback runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V250_STAGE execute=0'"
    diagnostic='  grep -E "^V254_NAND_CHILD guest=[01] caller=[01] reply=[01] mapped=[01] frame=[01] coherent=[01] text=[01] low=[01] sc=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$|^V254_NAND_GUEST callback=[01] next=[01] memory=[01] trial=([1-9]|1[0-6])$" "$work/v250-native.log" | sort -u || true'
    if s.count(fail)!=1:
        raise ValueError("V254 candidate failure diagnostic hook changed")
    s=s.replace(fail,diagnostic+'\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$work/v250-native.log" | sort -u
test "$(grep -Ec '{PASS}' "$work/v250-native.log")" -eq 16
test "$(grep -Ec '{TRIAL}' "$work/v250-native.log")" -eq 16
for n in $(seq 1 16); do
  grep -Fx "V254_NAND_GUEST callback=1 next=1 memory=1 trial=$n" "$work/v250-native.log"
done
echo 'V254_SC_NAND_FIRST_CHILD verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
