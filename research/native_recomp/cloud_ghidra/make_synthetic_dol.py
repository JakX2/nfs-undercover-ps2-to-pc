#!/usr/bin/env python3
"""Independently authored, tiny Wii DOL for public Ghidra CI. No game code."""
from __future__ import annotations

import argparse
from pathlib import Path
import struct

ENTRY = 0x8000403C
HELPER = ENTRY + 0x14
WORDS = (
    0x48000015,  # BL +0x14 (this independently authored fixture only)
    0x4E800020,  # BLR
    0x60000000,  # NOP padding
    0x60000000,
    0x60000000,
    0x3860002A,  # LI r3, 42
    0x4E800020,  # BLR
)


def make_dol() -> bytes:
    header = bytearray(256)
    program = struct.pack(">" + "I" * len(WORDS), *WORDS)
    struct.pack_into(">I", header, 0x00, 0x100)    # text section 0 file offset
    struct.pack_into(">I", header, 0x48, ENTRY)    # text section 0 guest address
    struct.pack_into(">I", header, 0x90, len(program))
    struct.pack_into(">I", header, 0xE0, ENTRY)    # guest entry point
    assert HELPER == ENTRY + 5 * 4
    return bytes(header) + program


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("refusing to overwrite an existing file")
    args.output.write_bytes(make_dol())
    print("PASS: original-free synthetic DOL generated")


if __name__ == "__main__":
    main()
