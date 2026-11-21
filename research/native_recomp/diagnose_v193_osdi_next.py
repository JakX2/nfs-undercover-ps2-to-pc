#!/usr/bin/env python3
"""V193 bounded public original-free assertion classifier."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v193_osdi_next_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:raise ValueError("V193 index outside public bounds")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text()
    labels=sorted(set(STRING.findall(derive(source))))
    if index>len(labels):raise ValueError("V193 index missing")
    return labels[index-1]

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index",type=int)
    a=parser.parse_args()
    print(f"V193_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
