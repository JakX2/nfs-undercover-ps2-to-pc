#!/usr/bin/env python3
"""Decode public-only V103 assertion identifiers; never read private job logs."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v103_sc_async_entry_harness import derive
def describe(index:int)->str:
    if index<1:raise ValueError("assertion ID must be positive")
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    labels=sorted(set(STRING.findall(derive(base.read_text(encoding="utf-8")))))
    if index>len(labels):raise ValueError("assertion ID exceeds public catalog")
    return labels[index-1]
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("id",type=int)
    args=p.parse_args()
    print(f"V103_PUBLIC_ASSERTION id={args.id:03d} label={describe(args.id)}")
