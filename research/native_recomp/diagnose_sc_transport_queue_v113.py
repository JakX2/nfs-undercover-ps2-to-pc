#!/usr/bin/env python3
"""Resolve V113 native assertion IDs using the generated public harness only."""
from pathlib import Path
import argparse
from classify_v38_native_failure import STRING
from derive_v113_sc_transport_queue_harness import derive


def describe(index: int) -> str:
    if index < 1:
        raise ValueError("V113 assertion ID must be positive")
    source = Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    messages = sorted(set(STRING.findall(derive(source))))
    if index > len(messages):
        raise ValueError("V113 assertion ID beyond public catalog")
    return messages[index - 1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id", type=int)
    args = parser.parse_args()
    print(f"V113_PUBLIC_ASSERTION id={args.id:03d} label={describe(args.id)}")
