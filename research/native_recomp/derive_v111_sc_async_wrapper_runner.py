#!/usr/bin/env python3
"""V111 native continuation through original SC async wrapper to IOS_OpenAsync."""
import argparse
from pathlib import Path
from derive_v110_sc_strlen_runner import derive as previous
def derive(source):
    s=previous(source)
    for old,new in (
        ("derive_v110_sc_strlen_harness.py","derive_v111_sc_async_wrapper_harness.py"),
        ("V110_TRIAL_PASS","V111_TRIAL_PASS"),
        ("V110 recovered continuous original __start->nonempty SC strlen continuation assertions",
         "V111 recovered continuous original __start->nonempty SC IOS_OpenAsync entry assertions"),
        ("stop=0x(8051e518|804f1e2c|8051e3dc)","stop=0x8051982c"),
        ("V110_STAGE native_test_passed","V111_STAGE native_test_passed"),
        ("V110_NATIVE_EXIT","V111_NATIVE_EXIT"),
        ("V110_HARNESS_MARKERS count=4","V110_HARNESS_MARKERS count=4"),
    ):
        if old==new:continue
        if old not in s:raise ValueError("V111 runner anchor missing: "+old)
        s=s.replace(old,new)
    # Stop only after the original asynchronous wrapper has executed its
    # allocator and guest pathname copy. Do not assume an IOS response.
    needle="grep -Eq '^V110_SC_CONTINUE route=1 data=1 abi=1 prior=1 branch=[123]$' \"$log\""
    if s.count(needle)!=1:raise ValueError("V111 original branch selection checkpoint missing")
    s=s.replace(needle,needle.replace("branch=[123]","branch=2")+"""
grep -Fxq 'V111_SC_ASYNC_ENTRY route=1 copied=1 path=1 nonempty=1 abi=1 prior=1' "$log" """.rstrip(),1)
    old='echo "BOOT_PROGRESS entry=0x8000403C pc=$target stage=110"'
    new='test "$branch" = 2\necho \'BOOT_PROGRESS entry=0x8000403C pc=0x8051982C stage=111\''
    if s.count(old)!=1:raise ValueError("V111 boot marker anchor missing")
    s=s.replace(old,new)
    old='echo \'V110_SC_CONTINUE route=1'
    # Keep all V110 source-provenance diagnostics intact.
    marker="echo 'V111_STAGE native_test_passed'"
    if s.count(marker)!=1:raise ValueError("V111 pass marker missing")
    s=s.replace(marker,marker+"\ngrep -E '^V111_SC_ASYNC_ENTRY route=[01] copied=[01] path=[01] nonempty=[01] abi=[01] prior=[01]$' \"$log\" | sort -u")
    return s
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
