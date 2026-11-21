#!/usr/bin/env python3
"""V185 map source-only native failure assertion IDs without owner game bytes."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v185_sc_reply_next_harness import derive

def describe(index: int)->str:
    if not 1<=index<=9999:
        raise ValueError("V185 native assertion index out of source catalog bounds")
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(source))))
    if index>len(labels):
        raise ValueError("V185 native assertion index outside original-free message catalog")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    args=p.parse_args()
    print(f"V185_PUBLIC_ASSERTION id={args.index:04d} label={describe(args.index)}")
