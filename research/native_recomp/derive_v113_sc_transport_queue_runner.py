#!/usr/bin/env python3
"""V113 continue original async IOS request to its next cache-flush call."""
import argparse
from pathlib import Path
from derive_v112_sc_async_submit_runner import derive as previous
def derive(source):
    s=previous(source)
    for old,new in (
        ("derive_v112_sc_async_submit_harness.py","derive_v113_sc_transport_queue_harness.py"),
        ("V112_TRIAL_PASS","V113_TRIAL_PASS"),
        ("V112 recovered continuous original __start->nonempty SC IOS_OpenAsync request assertions",
         "V113 recovered continuous original __start->SC IOS transport flush entry assertions"),
        ("stop=0x805195ec","stop=0x805222c0"),
        ("V112_STAGE native_test_passed","V113_STAGE native_test_passed"),
        ("V112_NATIVE_EXIT","V113_NATIVE_EXIT"),
        ("BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=112",
         "BOOT_PROGRESS entry=0x8000403C pc=0x805222C0 stage=113"),
    ):
        if old not in s:raise ValueError("V112 runner source anchor missing: "+old)
        s=s.replace(old,new)
    need="echo 'V113_STAGE native_test_passed'"
    if s.count(need)!=1:raise ValueError("V112 pass marker differs")
    s=s.replace(need,need+"""
grep -Fxq 'V112_ASYNC_SUBMIT route=1 wire=1 mode=1 path=1 abi=1 prior=1' "$log"
grep -Fx 'V113_FLUSH_ENTRY route=1 span=1 abi=1 prior=1' "$log"
grep -E '^V112_ASYNC_SYSCALL order=[01] lines=[01]$|^V112_ASYNC_SUBMIT route=[01] wire=[01] mode=[01] path=[01] abi=[01] prior=[01]$' "$log" | sort -u""")
    return s
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
