#!/usr/bin/env python3
"""V116 original IOS request queue-helper entry after native interrupt-disable."""
import argparse
from pathlib import Path
from derive_v115_sc_irq_disable_runner import derive as previous

EDITS = [
 ("derive_v115_sc_irq_disable_harness.py","derive_v116_sc_queue_helper_harness.py"),
 ("V115_TRIAL_PASS","V116_TRIAL_PASS"),
 ("V115 recovered continuous original __start->SC IOS request cache syscall return and IRQ-disable entry assertions",
  "V116 recovered continuous original __start->SC IOS IRQ-disable return and queue-helper entry assertions"),
 ("stop=0x805265ac","stop=0x8051afe0"),
 ("V115_STAGE native_test_passed","V116_STAGE native_test_passed"),
 ("V115_NATIVE_EXIT","V116_NATIVE_EXIT"),
 ("BOOT_PROGRESS entry=0x8000403C pc=0x805265AC stage=115",
  "BOOT_PROGRESS entry=0x8000403C pc=0x8051AFE0 stage=116"),
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        if old not in s:
            raise ValueError("V116 runner missing source anchor: "+old)
        s=s.replace(old,new)
    needle="echo 'V116_STAGE native_test_passed'"
    if s.count(needle)!=1:
        raise ValueError("V116 runner pass-marker ambiguity")
    return s.replace(needle,needle+"""
grep -Fx 'V116_QUEUE_HELPER route=1 pointer=1 abi=1 prior=1' "$log" """.rstrip())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
