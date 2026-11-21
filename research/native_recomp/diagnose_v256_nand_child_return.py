#!/usr/bin/env python3
"""V256 bounded public assertion label lookup without owner game source."""
import argparse
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v256_nand_child_return_harness import derive
from classify_v38_native_failure import STRING

def describe(index:int)->str:
    if not 1<=index<=9999:
        raise ValueError("V256 public assertion index outside supported bounds")
    src=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    labels=sorted(set(STRING.findall(derive(base(src.read_text(encoding="utf-8"))))))
    if index>len(labels):
        raise ValueError("V256 original-free assertion not found")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V256_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
