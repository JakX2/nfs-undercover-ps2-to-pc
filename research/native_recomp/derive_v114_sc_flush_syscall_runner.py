#!/usr/bin/env python3
"""V114 verify authentic IOS request cache syscall after original flush body."""
import argparse
from pathlib import Path
from derive_v113_sc_transport_queue_runner import derive as previous

EDITS = [
    ("derive_v113_sc_transport_queue_harness.py",
     "derive_v114_sc_flush_syscall_harness.py"),
    ("V113_TRIAL_PASS", "V114_TRIAL_PASS"),
    ("V113 recovered continuous original __start->SC IOS transport flush entry assertions",
     "V114 recovered continuous original __start->SC IOS request flush syscall entry assertions"),
    ("stop=0x805222c0", "stop=0x805222e8"),
    ("V113_STAGE native_test_passed", "V114_STAGE native_test_passed"),
    ("V113_NATIVE_EXIT", "V114_NATIVE_EXIT"),
    ("BOOT_PROGRESS entry=0x8000403C pc=0x805222C0 stage=113",
     "BOOT_PROGRESS entry=0x8000403C pc=0x805222E8 stage=114"),
]

def derive(source):
    s=previous(source)
    for old,new in EDITS:
        count=s.count(old)
        if count!=1:
            raise ValueError("V114 runner anchor missing or ambiguous: "+old+" count="+str(count))
        s=s.replace(old,new,1)
    need="echo 'V114_STAGE native_test_passed'"
    if s.count(need)!=1:
        raise ValueError("V114 pass marker missing")
    s=s.replace(need, need+"""
grep -Fx 'V114_CACHE_SYSCALL route=1 flushed=1 abi=1 prior=1' "$log" """.rstrip())
    return s

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    with args.output.open("x",encoding="utf-8") as f:
        f.write(derive(args.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
