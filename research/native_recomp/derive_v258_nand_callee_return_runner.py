#!/usr/bin/env python3
"""V258 owner-native original NAND successor call to PPC BLR return."""
import argparse
from pathlib import Path
from derive_v257_nand_postchild_runner import derive as previous

OLD='python3 "$V110_SOURCE_ROOT/derive_v257_nand_postchild_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v258_nand_callee_return_harness.py"'
DONE="echo 'V257_SC_NAND_POSTCHILD verified=1'"
PATTERN=r'^V258_NAND_CALLEE_RETURN guest=[01] mapped=[01] reply=[01] pending=[01] coherent=[01] sc=[0-9]{1,3}$'
PASS=r'^V258_NAND_CALLEE_RETURN guest=1 mapped=1 reply=[01] pending=[01] coherent=1 sc=[0-9]{1,3}$'
TRIAL=r'^V258_NAND_GUEST callback=1 returned=1 memory=1 trial=([1-9]|1[0-6])$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V258 inherited authentic V257 postchild runner changed")
    s=s.replace(OLD,NEW,1)
    legacy="V257_NAND_GUEST callback=1 next=1 memory=1"
    current="V258_NAND_GUEST callback=1 returned=1 memory=1"
    if s.count(legacy)!=7:
        raise ValueError("V258 inherited V257 final-state gate count changed")
    s=s.replace(legacy,current)
    fail="  echo 'V250_STAGE execute=0'"
    diag='  grep -E "^V258_NAND_CALLEE_RETURN guest=[01] mapped=[01] reply=[01] pending=[01] coherent=[01] sc=[0-9]{1,3}$|^V258_NAND_GUEST callback=[01] returned=[01] memory=[01] trial=([1-9]|1[0-6])$" "$work/v250-native.log" | sort -u || true'
    if s.count(fail)!=1:
        raise ValueError("V258 native failure observer changed")
    s=s.replace(fail,diag+'\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$work/v250-native.log" | sort -u
test "$(grep -Ec '{PASS}' "$work/v250-native.log")" -eq 16
test "$(grep -Ec '{TRIAL}' "$work/v250-native.log")" -eq 16
for n in $(seq 1 16); do
  grep -Fx "V258_NAND_GUEST callback=1 returned=1 memory=1 trial=$n" "$work/v250-native.log"
done
echo 'V258_SC_NAND_CALLEE_RETURN verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
