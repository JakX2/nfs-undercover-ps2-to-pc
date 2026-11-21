#!/usr/bin/env python3
"""V246 bounded assertion lookup from public original-free C++ harness."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v246_sc_nand_second_callback_harness import derive

def describe(index:int)->str:
    if not 1<=index<=9999:
        raise ValueError("V246 bounded index invalid")
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    names=sorted(set(STRING.findall(derive(base))))
    if index>len(names):
        raise ValueError("V246 bounded index absent")
    return names[index-1]

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("index",type=int)
    args=cli.parse_args()
    print(f"V246_PUBLIC_ASSERTION id={args.index:04d} label={describe(args.index)}")
