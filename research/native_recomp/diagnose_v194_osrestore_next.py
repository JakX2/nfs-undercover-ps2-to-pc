#!/usr/bin/env python3
"""V194 independent public-source assertion catalogue for private runner."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v194_osrestore_next_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:raise ValueError("V194 assertion out of range")
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text()
    labels=sorted(set(STRING.findall(derive(base))))
    if index>len(labels):raise ValueError("V194 public assertion missing")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    args=p.parse_args()
    print(f"V194_PUBLIC_ASSERTION id={args.index:04d} label={describe(args.index)}")
