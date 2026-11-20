#!/usr/bin/env python3
"""Map a V145 source-owned native assertion ID without original game bytes."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v145_sc_ipc_handler_harness import derive

def describe(index:int)->str:
    if index<1:raise ValueError("native assertion index must be positive")
    src=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(src))))
    if index>len(labels):raise ValueError("native assertion outside public catalog")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V145_PUBLIC_ASSERTION id={a.index:03d} label={describe(a.index)}")
