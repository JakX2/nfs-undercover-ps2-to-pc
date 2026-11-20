#!/usr/bin/env python3
"""Map source-owned V129 diagnostic assertion IDs without publishing owner game bytes."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v129_irq_disable_harness import derive

def describe(index:int)->str:
    if index<1:
        raise ValueError("V129 assertion ID must be positive")
    src=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(src))))
    if index>len(labels):
        raise ValueError("V129 assertion ID outside public catalog")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("id",type=int)
    a=p.parse_args()
    print(f"V129_PUBLIC_ASSERTION id={a.id:03d} label={describe(a.id)}")
