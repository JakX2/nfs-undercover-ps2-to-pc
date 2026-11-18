#!/usr/bin/env python3
"""Decode only source-owned assertion IDs, never read private runner logs."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v100_sc_status_harness import derive

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("id",type=int)
    a=p.parse_args()
    if a.id<1:raise SystemExit("assertion id must be positive")
    base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
    strings=sorted(set(STRING.findall(derive(base.read_text(encoding="utf-8")))))
    if a.id>len(strings):raise SystemExit("assertion id outside source catalog")
    print(f"V100_PUBLIC_ASSERTION id={a.id:03d} label={strings[a.id-1]}")
if __name__=="__main__":main()
