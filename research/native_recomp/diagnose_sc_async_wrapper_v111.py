#!/usr/bin/env python3
"""Resolve numeric native assertion IDs using V111 original-free diagnostics only."""
from pathlib import Path
import argparse
from classify_v38_native_failure import STRING
from derive_v111_sc_async_wrapper_harness import derive
def describe(index:int)->str:
    if index<1:raise ValueError("V111 assertion ID must be positive")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    messages=sorted(set(STRING.findall(derive(source))))
    if index>len(messages):raise ValueError("V111 assertion ID beyond public catalog")
    return messages[index-1]
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("id",type=int);a=p.parse_args()
    print(f"V111_PUBLIC_ASSERTION id={a.id:03d} label={describe(a.id)}")
