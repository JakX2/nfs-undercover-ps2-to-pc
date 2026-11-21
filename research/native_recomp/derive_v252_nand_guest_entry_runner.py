#!/usr/bin/env python3
"""V252 owner-original verified isolated NAND callback bctrl-entry proof."""
import argparse
from pathlib import Path
from derive_v250_restored_callback_nand_runner import derive as previous

OLD='python3 "$V110_SOURCE_ROOT/derive_v250_restored_callback_nand_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v252_nand_guest_entry_harness.py"'
DONE="echo 'V250_SC_NAND_BCTRL verified=1'"
PATTERN=r'^V252_NAND_GUEST checked=[01] regs=[01] reply=[01] before_second=[01] trial=([1-9]|1[0-6])$'
PASS=r'^V252_NAND_GUEST checked=1 regs=1 reply=1 before_second=1 trial=([1-9]|1[0-6])$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V252 inherited original restored callback run changed")
    s=s.replace(OLD,NEW,1)
    failure="  echo 'V250_STAGE execute=0'"
    diagnostic='  grep -E "^V252_NAND_GUEST checked=[01] regs=[01] reply=[01] before_second=[01] trial=([1-9]|1[0-6])$" "$work/v250-native.log" | sort -u || true'
    if s.count(failure)!=1:
        raise ValueError("V252 inherited candidate execute failure seam changed")
    s=s.replace(failure,diagnostic+'\n'+failure,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$work/v250-native.log" | sort -u
test "$(grep -Ec '{PASS}' "$work/v250-native.log")" -eq 16
for n in $(seq 1 16); do
  grep -Fx "V252_NAND_GUEST checked=1 regs=1 reply=1 before_second=1 trial=$n" "$work/v250-native.log"
done
echo 'V252_SC_NAND_GUEST verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
