#!/usr/bin/env python3
"""V257 continue owner-original NAND callback after V256 child return."""
import argparse
from pathlib import Path
from derive_v256_nand_child_return_runner import derive as previous

OLD='python3 "$V110_SOURCE_ROOT/derive_v256_nand_child_return_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v257_nand_postchild_harness.py"'
DONE="echo 'V256_SC_NAND_CHILD_RETURN verified=1'"
PATTERN=r'^V257_NAND_NEXT guest=[01] caller=[01] code=[01] mapped=[01] reply=[01] coherent=[01] sc=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V257_NAND_NEXT guest=1 caller=1 code=1 mapped=1 reply=[01] coherent=1 sc=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
TRIAL=r'^V257_NAND_GUEST callback=1 next=1 memory=1 trial=([1-9]|1[0-6])$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V257 authenticated V256 NAND return runner changed")
    s=s.replace(OLD,NEW,1)
    # V256's 16-trial stop-state gates are superseded by the next original
    # guest call. Both V254 inherited and V256 own gates must advance together.
    legacy="V256_NAND_GUEST callback=1 returned=1 memory=1"
    current="V257_NAND_GUEST callback=1 next=1 memory=1"
    if s.count(legacy)!=5:
        raise ValueError("V257 inherited V256 final-state gate count changed")
    s=s.replace(legacy,current)
    fail="  echo 'V250_STAGE execute=0'"
    diag='  grep -E "^V257_NAND_NEXT guest=[01] caller=[01] code=[01] mapped=[01] reply=[01] coherent=[01] sc=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$|^V257_NAND_GUEST callback=[01] next=[01] memory=[01] trial=([1-9]|1[0-6])$" "$work/v250-native.log" | sort -u || true'
    if s.count(fail)!=1:
        raise ValueError("V257 inherited native failure diagnostic changed")
    s=s.replace(fail,diag+'\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$work/v250-native.log" | sort -u
test "$(grep -Ec '{PASS}' "$work/v250-native.log")" -eq 16
test "$(grep -Ec '{TRIAL}' "$work/v250-native.log")" -eq 16
for n in $(seq 1 16); do
  grep -Fx "V257_NAND_GUEST callback=1 next=1 memory=1 trial=$n" "$work/v250-native.log"
done
echo 'V257_SC_NAND_POSTCHILD verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
