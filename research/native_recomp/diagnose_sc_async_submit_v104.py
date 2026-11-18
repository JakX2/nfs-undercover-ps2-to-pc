#!/usr/bin/env python3
"""Decode only source-owned V104 assertion IDs; never read private logs."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v104_sc_async_submit_harness import derive

def describe(index:int)->str:
    if index<1:raise ValueError("assertion ID must be positive")
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    names=sorted(set(STRING.findall(derive(base.read_text(encoding="utf-8")))))
    if index>len(names):raise ValueError("assertion ID exceeds public catalog")
    return names[index-1]
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("id",type=int)
    a=p.parse_args();print(f"V104_PUBLIC_ASSERTION id={a.id:03d} label={describe(a.id)}")
