#!/usr/bin/env python3
"""V191 bounded source-only legacy diagnostic mapping (private logs excluded)."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v191_second_ios_next_harness import derive
def describe(index: int)->str:
    if not 1<=index<=9999:raise ValueError("V191 public assertion index out of range")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text()
    a=sorted(set(STRING.findall(derive(source))))
    if index>len(a):raise ValueError("V191 public assertion not found")
    return a[index-1]
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V191_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
