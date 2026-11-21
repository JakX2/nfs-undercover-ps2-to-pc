#!/usr/bin/env python3
"""V200 bounded public assertion classifier without private game content."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v200_sc_y2_ipc_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:
        raise ValueError("V200 public assertion index outside bounds")
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    labels=sorted(set(STRING.findall(derive(base.read_text(encoding="utf-8")))))
    if index>len(labels):
        raise ValueError("V200 public assertion not found")
    return labels[index-1]

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index",type=int)
    args=parser.parse_args()
    print(f"V200_PUBLIC_ASSERTION id={args.index:04d} label={describe(args.index)}")
