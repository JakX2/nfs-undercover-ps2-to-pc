#!/usr/bin/env python3
"""Map public V184 native assertion IDs to original-free assertion labels.

The numeric ID comes from the private owner CI, but the catalog and labels
are extracted solely from independently authored test harness source. No
proprietary binary bytes, translated game code, register data or IOS payload
are printed.
"""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v184_sc_reply_burst_harness import derive

def describe(index: int)->str:
    if not 1<=index<=9999:
        raise ValueError("V184 public assertion ID out of bounds")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(source))))
    if index>len(labels):
        raise ValueError("V184 assertion ID outside public message catalog")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V184_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
