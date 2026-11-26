#!/usr/bin/env python3
"""Generate a private sized NWiiRecomp function map from a SHA-pinned Wii ELF.

The CSV never leaves private runner scratch and contains anonymized labels.
This original-free implementation uses only Python's standard library.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

ORIGINAL_SHA256 = "fd9681f2b06e961667bcad2eea6aaf6c762e0f30d666376d1ebb5f2946455ab0"
HEADER = struct.Struct(">16sHHIIIIIHHHHHH")
SECTION = struct.Struct(">IIIIIIIIII")
SYMBOL = struct.Struct(">IIIBBH")
ENTRY = 0x8000403C


from functools import lru_cache

@lru_cache(maxsize=2)
def _parse_function_items(data: bytes) -> tuple[tuple[int,int], ...]:
    if len(data) < HEADER.size:
        raise ValueError("ELF header truncated")
    head = HEADER.unpack_from(data)
    ident, _, machine, version, _, _, shoff, _, ehsize, _, _, shentsize, shnum, _ = head
    if (ident[:7] != b"\x7fELF\x01\x02\x01" or machine != 20 or version != 1
            or ehsize != HEADER.size or shentsize != SECTION.size
            or not 0 < shnum < 10000 or not shoff
            or shoff + shnum * SECTION.size > len(data)):
        raise ValueError("expected bounded big-endian ELF32 PowerPC sections")
    sections = [SECTION.unpack_from(data, shoff + i * SECTION.size) for i in range(shnum)]
    result: dict[int, int] = {}
    symtab_count = 0
    for section in sections:
        _, kind, _, _, offset, size, _, _, _, entsize = section
        if kind != 2:
            continue
        symtab_count += 1
        if (entsize != SYMBOL.size or size % SYMBOL.size
                or offset + size > len(data) or size > 16 * 1024 * 1024):
            raise ValueError("ELF symbol table geometry invalid")
        for at in range(offset, offset + size, SYMBOL.size):
            _, addr, nbytes, info, _, shndx = SYMBOL.unpack_from(data, at)
            if ((info & 15) != 2 or shndx == 0 or nbytes == 0
                    or addr & 3 or nbytes & 3 or addr < 0x80000000
                    or addr + nbytes > 0x94000000):
                continue
            result[addr] = max(result.get(addr, 0), nbytes)
    if not symtab_count or ENTRY not in result:
        raise ValueError("missing original function symbol table or startup")
    return tuple(sorted(result.items()))


def parse_functions(data: bytes) -> dict[int, int]:
    # Cache only immutable bytes, and never expose the cached result to a
    # caller that may modify a map. Cache lifetime is the private process.
    if type(data) is bytes:
        return dict(_parse_function_items(data))
    return dict(_parse_function_items.__wrapped__(data))


def csv_lines(functions: dict[int, int]) -> str:
    if not functions:
        raise ValueError("no validated function entries")
    return "Name,Location,Size\n" + "".join(
        f"fn_{pc:08X},{pc:08X},{length}\n" for pc, length in sorted(functions.items())
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument("output", type=Path, help="new private CSV path")
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("refusing to overwrite private symbol map")
    raw = args.elf.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA256:
        parser.error("Wii ELF SHA-256 mismatch")
    functions = parse_functions(raw)
    if len(functions) < 25000:
        parser.error("too few ELF function entries for owner Wii image")
    import os
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as target:
        target.write(csv_lines(functions))
    print(f"PASS: original PowerPC ELF map prepared privately; functions={len(functions)}")


if __name__ == "__main__":
    main()
