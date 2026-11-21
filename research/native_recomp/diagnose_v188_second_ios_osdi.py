#!/usr/bin/env python3
"""V188 original-free assertion labels for private owner native test failures."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v188_second_ios_osdi_harness import derive
def describe(index:int)->str:
    if not 1<=index<=9999:raise ValueError("V188 invalid public assertion ID")
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels=sorted(set(STRING.findall(derive(base))))
    if index>len(labels):raise ValueError("V188 ID outside source-owned labels")
    return labels[index-1]
if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("index",type=int)
    a=ap.parse_args()
    print(f"V188_PUBLIC_ASSERTION id={a.index:04d} label={describe(a.index)}")
