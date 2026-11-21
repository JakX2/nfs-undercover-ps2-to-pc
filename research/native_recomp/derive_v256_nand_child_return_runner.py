#!/usr/bin/env python3
"""V256 original Wii NAND child function return to genuine PPC caller."""
import argparse
from pathlib import Path
from derive_v254_nand_first_child_runner import derive as previous

OLD='python3 "$V110_SOURCE_ROOT/derive_v254_nand_first_child_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v256_nand_child_return_harness.py"'
DONE="echo 'V254_SC_NAND_FIRST_CHILD verified=1'"
PATTERN=r'^V256_NAND_RETURN child=[01] guest=[01] frame=[01] reply=[01] mapped=[01] pending=[01] coherent=[01] sc=[0-9]{1,3}$'
PASS=r'^V256_NAND_RETURN child=1 guest=1 frame=1 reply=1 mapped=1 pending=1 coherent=1 sc=[0-9]{1,3}$'
TRIAL=r'^V256_NAND_GUEST callback=1 returned=1 memory=1 trial=([1-9]|1[0-6])$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V256 verified V254 original NAND runner changed")
    s=s.replace(OLD,NEW,1)
    # V254 only stopped at the first guest child call. V256 resumes that
    # child and replaces V254's final guest assertion with the natural
    # PowerPC return assertion. Its old 16-trial final-state gate must
    # therefore advance with the observer; the V254 CHILD entry test stays.
    legacy_trial=r'^V254_NAND_GUEST callback=1 next=1 memory=1 trial=([1-9]|1[0-6])
    diag='  grep -E "^V256_NAND_RETURN child=[01] guest=[01] frame=[01] reply=[01] mapped=[01] pending=[01] coherent=[01] sc=[0-9]{1,3}$|^V256_NAND_GUEST callback=[01] returned=[01] memory=[01] trial=([1-9]|1[0-6])$" "$work/v250-native.log" | sort -u || true'
    if s.count(fail)!=1:
        raise ValueError("V256 previous candidate failure hook changed")
    s=s.replace(fail,diag+'\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$work/v250-native.log" | sort -u
test "$(grep -Ec '{PASS}' "$work/v250-native.log")" -eq 16
test "$(grep -Ec '{TRIAL}' "$work/v250-native.log")" -eq 16
for n in $(seq 1 16); do
  grep -Fx "V256_NAND_GUEST callback=1 returned=1 memory=1 trial=$n" "$work/v250-native.log"
done
echo 'V256_SC_NAND_CHILD_RETURN verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

    legacy_count=f"""test "$(grep -Ec '{legacy_trial}' "$work/v250-native.log")" -eq 16"""
    current_count=f"""test "$(grep -Ec '{TRIAL}' "$work/v250-native.log")" -eq 16"""
    legacy_row='  grep -Fx "V254_NAND_GUEST callback=1 next=1 memory=1 trial=$n" "$work/v250-native.log"'
    current_row='  grep -Fx "V256_NAND_GUEST callback=1 returned=1 memory=1 trial=$n" "$work/v250-native.log"'
    if s.count(legacy_count)!=1 or s.count(legacy_row)!=1:
        raise ValueError("V256 inherited V254 final-state gates changed")
    s=s.replace(legacy_count,current_count,1)
    s=s.replace(legacy_row,current_row,1)
    fail="  echo 'V250_STAGE execute=0'"
    diag='  grep -E "^V256_NAND_RETURN child=[01] guest=[01] frame=[01] reply=[01] mapped=[01] pending=[01] coherent=[01] sc=[0-9]{1,3}$|^V256_NAND_GUEST callback=[01] returned=[01] memory=[01] trial=([1-9]|1[0-6])$" "$work/v250-native.log" | sort -u || true'
    if s.count(fail)!=1:
        raise ValueError("V256 previous candidate failure hook changed")
    s=s.replace(fail,diag+'\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$work/v250-native.log" | sort -u
test "$(grep -Ec '{PASS}' "$work/v250-native.log")" -eq 16
test "$(grep -Ec '{TRIAL}' "$work/v250-native.log")" -eq 16
for n in $(seq 1 16); do
  grep -Fx "V256_NAND_GUEST callback=1 returned=1 memory=1 trial=$n" "$work/v250-native.log"
done
echo 'V256_SC_NAND_CHILD_RETURN verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
