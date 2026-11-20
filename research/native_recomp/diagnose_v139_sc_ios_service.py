#!/usr/bin/env python3
"""Resolve V139 source-owned native assertion IDs without publishing original data."""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v139_sc_ios_service_harness import derive


def describe(index: int) -> str:
    if index < 1:
        raise ValueError("V139 assertion ID must be positive")
    source = Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    labels = sorted(set(STRING.findall(derive(source))))
    if index > len(labels):
        raise ValueError("V139 assertion ID outside public catalog")
    return labels[index-1]


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("id",type=int)
    args = p.parse_args()
    print(f"V139_PUBLIC_ASSERTION id={args.id:03d} label={describe(args.id)}")
