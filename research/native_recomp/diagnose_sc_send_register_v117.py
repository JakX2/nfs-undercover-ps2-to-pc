#!/usr/bin/env python3
"""Map V117 original-free assertion labels to an owner-private failure code."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v117_sc_send_register_harness import derive

def describe(index:int)->str:
    if index<1:
        raise ValueError("V117 assertion ID must be positive")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(source))))
    if index>len(labels):
        raise ValueError("V117 assertion ID beyond public catalog")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("id",type=int)
    a=p.parse_args()
    print(f"V117_PUBLIC_ASSERTION id={a.id:03d} label={describe(a.id)}")
