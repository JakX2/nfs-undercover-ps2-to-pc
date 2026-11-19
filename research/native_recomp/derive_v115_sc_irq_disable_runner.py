#!/usr/bin/env python3
"""V115 derive private original boot runner with authentic async cache syscall return and IRQ-disable entry."""
import argparse
from pathlib import Path
from derive_v114_sc_flush_syscall_runner import derive as previous

EDITS = [
 ("derive_v114_sc_flush_syscall_harness.py","derive_v115_sc_irq_disable_harness.py"),
 ("V114_TRIAL_PASS","V115_TRIAL_PASS"),
 ("V114 recovered continuous original __start->SC IOS request flush syscall entry assertions",
  "V115 recovered continuous original __start->SC IOS request cache syscall return and IRQ-disable entry assertions"),
 ("stop=0x805222e8","stop=0x805265ac"),
 ("V114_STAGE native_test_passed","V115_STAGE native_test_passed"),
 ("V114_NATIVE_EXIT","V115_NATIVE_EXIT"),
 ("BOOT_PROGRESS entry=0x8000403C pc=0x805222E8 stage=114",
  "BOOT_PROGRESS entry=0x8000403C pc=0x805265AC stage=115"),
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        count=s.count(old)
        if count<1:
            raise ValueError("V115 runner source anchor missing: "+old)
        s=s.replace(old,new)
    need="echo 'V115_STAGE native_test_passed'"
    if s.count(need)!=1:
        raise ValueError("V115 pass marker missing or ambiguous")
    s=s.replace(need,need+"""
grep -Fx 'V115_VECTOR_ENTRY valid=1' "$log"
grep -Fx 'V115_DISABLE_ENTRY route=1 abi=1 prior=1' "$log" """.rstrip())
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
