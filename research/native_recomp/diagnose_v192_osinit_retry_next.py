#!/usr/bin/env python3
"""V192 public source-only classifier for bounded owner assertion indices."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v192_osinit_retry_next_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:raise ValueError("V192 public assertion out of range")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text()
    names=sorted(set(STRING.findall(derive(source))))
    if index>len(names):raise ValueError("V192 assertion index missing")
    return names[index-1]

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index",type=int)
    args=parser.parse_args()
    print(f"V192_PUBLIC_ASSERTION id={args.index:04d} label={describe(args.index)}")
