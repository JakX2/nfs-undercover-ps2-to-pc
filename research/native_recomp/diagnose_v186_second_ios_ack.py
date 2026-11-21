#!/usr/bin/env python3
"""V186 public source-only original native assertion catalog."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v186_second_ios_ack_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:
        raise ValueError("V186 original-free assertion ID outside limits")
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(base))))
    if index>len(labels):
        raise ValueError("V186 assertion not in public authored source")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V186_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
