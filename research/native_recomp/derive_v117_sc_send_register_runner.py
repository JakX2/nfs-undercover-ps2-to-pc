#!/usr/bin/env python3
"""V117 native original IPC send-register call after authentic queue helper."""
import argparse
from pathlib import Path
from derive_v116_sc_queue_helper_runner import derive as previous

EDITS = [
 ("derive_v116_sc_queue_helper_harness.py","derive_v117_sc_send_register_harness.py"),
 ("V116_TRIAL_PASS","V117_TRIAL_PASS"),
 ("V116 recovered continuous original __start->SC IOS IRQ-disable return and queue-helper entry assertions",
  "V117 recovered continuous original __start->SC IOS queue-helper return and IPC send-register entry assertions"),
 ("stop=0x8051afe0","stop=0x8051906c"),
 ("V116_STAGE native_test_passed","V117_STAGE native_test_passed"),
 ("V116_NATIVE_EXIT","V117_NATIVE_EXIT"),
 ("BOOT_PROGRESS entry=0x8000403C pc=0x8051AFE0 stage=116",
  "BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=117"),
]

def derive(source):
    s=previous(source)
    for a,b in EDITS:
        if a not in s:
            raise ValueError("V117 runner source anchor missing: "+a)
        s=s.replace(a,b)
    need="echo 'V117_STAGE native_test_passed'"
    if s.count(need)!=1:
        raise ValueError("V117 pass marker absent/ambiguous")
    return s.replace(need,need+"""
grep -Fx 'V117_SEND_REG route=1 abi=1 prior=1' "$log" """.rstrip())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
