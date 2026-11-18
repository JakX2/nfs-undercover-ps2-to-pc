#!/usr/bin/env python3
"""Bounded original-owner DOL inventory for *public Wii SDK* config paths.

Never print strings read from the owner, offsets, addresses or binaries.
This identifies whether a reduced startup fixture omitted an initialized
public pathname; it does not assert a successful filesystem open.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_hardware_boundary_v17 import ORIGINAL_SHA
from make_private_elf_symbol_map import ORIGINAL_SHA256

PUBLIC = (
    ("sysconf_path", b"/shared2/sys/SYSCONF\0"),
    ("sysconf_leaf", b"SYSCONF\0"),
    ("setting_path", b"/shared2/sys/setting.txt\0"),
    ("fs_device", b"/dev/fs\0"),
    ("es_device", b"/dev/es\0"),
)
HEADER_SIZE = 256
MAX_SEGMENT = 32*1024*1024

def data_sections(dol: bytes):
    if len(dol) < HEADER_SIZE:
        raise ValueError("truncated DOL")
    seen = []
    for i in range(11):
        at = struct.unpack_from(">I", dol, 0x1c+4*i)[0]
        address = struct.unpack_from(">I", dol, 0x64+4*i)[0]
        size = struct.unpack_from(">I", dol, 0xac+4*i)[0]
        if not size:
            continue
        if size > MAX_SEGMENT or at < HEADER_SIZE or at+size > len(dol) or not (
            0x80000000 <= address < 0x94000000 and address+size <= 0x94000000
        ):
            raise ValueError("invalid bounded DOL initialized data section")
        if any(not (at+size<=start or end<=at) for start,end in seen):
            raise ValueError("overlapping DOL data section")
        seen.append((at,at+size))
        yield dol[at:at+size]

def counts(dol: bytes):
    segments = tuple(data_sections(dol))
    # Count matches entirely within one initialized data section.
    result = []
    for _,needle in PUBLIC:
        count = sum(section.count(needle) for section in segments)
        result.append(min(count,16))  # cap published counts
    return tuple(result)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dol", type=Path)
    parser.add_argument("elf", type=Path)
    args = parser.parse_args()
    dol = args.dol.read_bytes()
    elf = args.elf.read_bytes()
    if hashlib.sha256(dol).hexdigest()!=ORIGINAL_SHA or (
        hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256
    ):
        raise ValueError("authenticated owner image digest mismatch")
    for (label,_),value in zip(PUBLIC, counts(dol)):
        print(f"V106_SC_LITERAL label={label} count={value}")
    print("PASS: bounded owner-original public SC pathname inventory")

if __name__ == "__main__":
    main()
