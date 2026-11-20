#!/usr/bin/env python3
"""Decode V149 owner-private numeric assertion using original-free test strings.

The caller supplies only the bounded public assertion ID. No Wii game code,
private native logs, translated output or executable bytes are exposed.
"""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v149_sc_ipc_ack_harness import derive

def describe(index: int)->str:
    if not 1<=index<=999:
        raise ValueError("V149 assertion index outside numeric safety bound")
    src=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(src))))
    if index>len(labels):
        raise ValueError("V149 assertion ID outside public harness catalog")
    return labels[index-1]

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    args=p.parse_args()
    print(f"V149_PUBLIC_ASSERTION id={args.index:03d} label={describe(args.index)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
