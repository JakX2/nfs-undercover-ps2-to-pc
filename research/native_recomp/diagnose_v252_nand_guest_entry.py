#!/usr/bin/env python3
"""V252 bounded public-only compiled-candidate native assertion lookup."""
import argparse
from pathlib import Path
from diagnose_v250_native_phase import describe as previous
from derive_v244_sc_callback_link_harness import derive as original
from derive_v252_nand_guest_entry_harness import derive
from classify_v38_native_failure import STRING

def describe(index:int)->str:
    if not 1<=index<=9999:
        raise ValueError("V252 public assertion index outside bounds")
    src=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    text=derive(original(src.read_text(encoding="utf-8")))
    labels=sorted(set(STRING.findall(text)))
    if index>len(labels):
        raise ValueError("V252 public assertion does not exist")
    return labels[index-1]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V252_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
