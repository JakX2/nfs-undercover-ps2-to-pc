#!/usr/bin/env python3
"""Map V108 assertion IDs to original-free, publicly owned diagnostics."""
from pathlib import Path
import argparse
from classify_v38_native_failure import STRING
from derive_v108_sc_literal_restore_harness import derive

def describe(index: int)->str:
    source=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    messages=sorted(set(STRING.findall(derive(source))))
    if not 1<=index<=len(messages):raise ValueError("invalid V108 public assertion ID")
    return messages[index-1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("id",type=int)
    a=p.parse_args()
    print(f"V108_PUBLIC_ASSERTION id={a.id:03d} label={describe(a.id)}")

if __name__=="__main__":main()
