#!/usr/bin/env python3
"""V199 source-only original-free bounded owner assertion classifier."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v199_sc_y2_disable_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:raise ValueError("V199 public assertion index outside bounds")
    s=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text()
    labels=sorted(set(STRING.findall(derive(s))))
    if index>len(labels):raise ValueError("V199 public assertion not found")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V199_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
