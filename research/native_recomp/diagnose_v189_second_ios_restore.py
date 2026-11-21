#!/usr/bin/env python3
"""V189 bounded owner-native source-only assertion catalog."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v189_second_ios_restore_harness import derive
def describe(n:int)->str:
    if not 1<=n<=9999:raise ValueError("V189 invalid original-free assertion ID")
    s=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(s))))
    if n>len(labels):raise ValueError("V189 original-free assertion outside source catalog")
    return labels[n-1]
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("index",type=int)
    a=p.parse_args()
    print(f"V189_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
