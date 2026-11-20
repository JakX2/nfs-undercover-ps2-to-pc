#!/usr/bin/env python3
"""Map private V153 assertion IDs to public source-owned diagnostics only.

Never accept, print, or upload owner-native logs or original game bytes.
"""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v153_sc_reply_handoff_harness import derive

def describe(index: int)->str:
    if not 1<=index<=999:
        raise ValueError("V153 assertion index outside public numeric bound")
    original=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    public=derive(original)
    labels=sorted(set(STRING.findall(public)))
    if index>len(labels):
        raise ValueError("V153 assertion index outside public label catalog")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V153_PUBLIC_ASSERTION id={a.index:03d} label={describe(a.index)}")
