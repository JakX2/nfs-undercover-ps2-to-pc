#!/usr/bin/env python3
"""V187 source-only native assertion ID mapping without private guest code."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v187_second_ios_next_harness import derive
def describe(index: int)->str:
    if not 1<=index<=9999:
        raise ValueError("V187 original-free assertion index invalid")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(source))))
    if index>len(labels):
        raise ValueError("V187 source-owned assertion outside catalog")
    return labels[index-1]
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    args=p.parse_args()
    print(f"V187_PUBLIC_ASSERTION id={args.index:04d} label={describe(args.index)}")
