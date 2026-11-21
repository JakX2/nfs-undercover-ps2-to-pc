#!/usr/bin/env python3
"""V226 source-only bounded owner assertion lookup."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v226_sc_y1_reply_successor_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:
        raise ValueError("V226 public assertion index outside bounds")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    labels=sorted(set(STRING.findall(derive(source.read_text(encoding="utf-8")))))
    if index>len(labels):
        raise ValueError("V226 public assertion not found")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    args=p.parse_args()
    print(f"V226_PUBLIC_ASSERTION id={args.index:04d} label={describe(args.index)}")
