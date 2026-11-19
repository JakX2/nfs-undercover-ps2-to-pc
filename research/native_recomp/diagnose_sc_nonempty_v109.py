#!/usr/bin/env python3
"""Decode V109 native assertion IDs from original-free public test strings."""
from pathlib import Path
import argparse
from classify_v38_native_failure import STRING
from derive_v109_sc_nonempty_harness import derive

def describe(index:int)->str:
    if index<1:raise ValueError("assertion ID must be positive")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    messages=sorted(set(STRING.findall(derive(source))))
    if index>len(messages):raise ValueError("assertion ID exceeds public catalog")
    return messages[index-1]

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id",type=int)
    a=parser.parse_args()
    print(f"V109_PUBLIC_ASSERTION id={a.id:03d} label={describe(a.id)}")
