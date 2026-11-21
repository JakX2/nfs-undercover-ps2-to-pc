#!/usr/bin/env python3
"""Classify V256 owner-log checkpoint formatting without exposing private logs.

Only public marker counts and positional properties are released. No log lines,
game paths, CPU state, generated code, or instruction bytes are printed.
"""
import argparse
import re
from pathlib import Path

MARKER = "V256_SC_NAND_CHILD_RETURN verified=1"
RETURN = re.compile(r"V256_NAND_RETURN child=1 guest=1 frame=1 reply=1 mapped=1 pending=1 coherent=1 sc=[0-9]{1,3}")
GUEST = re.compile(r"V256_NAND_GUEST callback=1 returned=1 memory=1 trial=([1-9]|1[0-6])")
SHAPE = re.compile(r"V256_SHAPE token=[0-9]{1,3} prefix=[0-9]{1,3} fields=[0-9]{1,3} exact=[0-9]{1,3} pass=[0-9]{1,3} guest=[0-9]{1,3}")

def classify(log: str) -> str:
    lines = log.splitlines()
    marker_lines = [line for line in lines if MARKER in line]
    return_lines = [line for line in lines if "V256_NAND_RETURN child=" in line]
    guest_lines = [line for line in lines if "V256_NAND_GUEST callback=" in line]
    shape_lines = [line for line in lines if "V256_SHAPE token=" in line]
    bounded = lambda value: min(value, 999)
    keys = {
        "marker_any": len(marker_lines),
        "marker_bol": sum(line.startswith(MARKER) for line in marker_lines),
        "marker_exact": sum(line == MARKER for line in marker_lines),
        "marker_trim": sum(line.strip() == MARKER for line in marker_lines),
        "return_any": len(return_lines),
        "return_exact": sum(bool(RETURN.fullmatch(line)) for line in return_lines),
        "guest_any": len(guest_lines),
        "guest_exact": sum(bool(GUEST.fullmatch(line)) for line in guest_lines),
        "shape_any": len(shape_lines),
        "shape_exact": sum(bool(SHAPE.fullmatch(line)) for line in shape_lines),
    }
    return "V256_SAFE_SHAPE " + " ".join(
        f"{name}={bounded(value)}" for name, value in keys.items()
    )

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("owner_log", type=Path)
    args = parser.parse_args()
    # The original log is ephemeral, privately staged and deleted by CI.
    print(classify(args.owner_log.read_text(encoding="utf-8", errors="replace")))

if __name__ == "__main__":
    main()
