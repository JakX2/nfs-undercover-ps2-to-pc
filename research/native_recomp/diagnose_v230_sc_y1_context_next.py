#!/usr/bin/env python3
"""V230 source-only bounded owner assertion lookup."""
import argparse
from pathlib import Path
import sys
sys.setrecursionlimit(6000)
import sys
# The public original-free V79-V230 source derivation chain is deep.
# Increase only this Python import/derivation budget, never the guest CPU budget.
sys.setrecursionlimit(6000)
from classify_v38_native_failure import STRING
from derive_v230_sc_y1_context_next_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:
        raise ValueError("V230 public assertion index outside bounds")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    labels=sorted(set(STRING.findall(derive(source.read_text(encoding="utf-8")))))
    if index>len(labels):
        raise ValueError("V230 public assertion not found")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    args=p.parse_args()
    print(f"V230_PUBLIC_ASSERTION id={args.index:04d} label={describe(args.index)}")
