#!/usr/bin/env python3
"""V113 continue verified original async IOS request to queue initializer."""
import argparse
from pathlib import Path
from derive_v112_sc_async_submit_runner import derive as previous
def derive(source):
    s=previous(source)
    for old,new in (
        ("derive_v111_sc_async_wrapper_harness.py","derive_v113_sc_transport_queue_harness.py"),
        ("V111_TRIAL_PASS","V113_TRIAL_PASS"),
        ("V111 recovered continuous original __start->nonempty SC IOS_OpenAsync entry assertions",
         "V113 recovered continuous original __start->SC IOS transport queue entry assertions"),
        ("stop=0x8051982c","stop=0x805293b0"),
        ("V111_STAGE native_test_passed","V113_STAGE native_test_passed"),
        ("V111_NATIVE_EXIT","V113_NATIVE_EXIT"),
        ("BOOT_PROGRESS entry=0x8000403C pc=0x8051982C stage=111",
         "BOOT_PROGRESS entry=0x8000403C pc=0x805293B0 stage=113"),
    ):
        if old not in s:raise ValueError("V112 runner source anchor missing: "+old)
        s=s.replace(old,new)
    need="echo 'V113_STAGE native_test_passed'"
    if s.count(need)!=1:raise ValueError("V112 pass marker differs")
    s=s.replace(need,need+"""
grep -Fxq 'V112_ASYNC_SUBMIT route=1 wire=1 mode=1 path=1 abi=1 prior=1' "$log"
grep -Fxq 'V113_QUEUE_ENTRY route=1 queue=1 abi=1 prior=1' "$log"
grep -E '^V112_ASYNC_SYSCALL order=[01] lines=[01]$|^V112_ASYNC_SUBMIT route=[01] wire=[01] mode=[01] path=[01] abi=[01] prior=[01]$' "$log" | sort -u""")
    return s
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
