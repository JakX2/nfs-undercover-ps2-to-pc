#!/usr/bin/env python3
"""Decode a V109 public assertion without accessing owner logs or binaries."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v109_sc_nonempty_harness import derive
def describe(index:int)->str:
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    labels=sorted(set(STRING.findall(derive(base.read_text(encoding="utf-8")))))
    if not 1<=index<=len(labels):raise ValueError("invalid V109 source-owned assertion ID")
    return labels[index-1]
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("id",type=int);a=p.parse_args()
    print(f"V109_PUBLIC_ASSERTION id={a.id:03d} label={describe(a.id)}")
