#!/usr/bin/env python3
"""V243: private owner Wii ELF PowerPC callback-to-ISFS branch audit.

Independently-written, read-only PPC32 branch classifier. The real ELF
is SHA-256 authenticated by make_private_elf_symbol_map and consumed
only inside the private owner's GitHub Actions scratch directory.
Print only bounded booleans, never PPC instruction words, bytes,
disassembly, symbol names, paths, or original code.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_private_elf_symbol_map import (
    HEADER, SECTION, ORIGINAL_SHA256, parse_functions,
)

CB = 0x804F0E04
ISFS = 0x804F1E2C
ISFS_PROLOGUE = 0x804F1E3C
TEXT_MIN = 0x80400000
TEXT_MAX = 0x80600000

def branch_target(pc: int, word: int) -> int | None:
    """Decode PPC 'b' and 'bc' immediate target with AA and sign extension."""
    op = word >> 26
    if op == 18:
        disp = word & 0x03FFFFFC
        if disp & 0x02000000:
            disp -= 0x04000000
    elif op == 16:
        disp = word & 0x0000FFFC
        if disp & 0x00008000:
            disp -= 0x00010000
    else:
        return None
    aa = bool(word & 2)
    return (disp if aa else pc + disp) & 0xFFFFFFFF

def classify_words(callback_pc: int, words: list[int], isfs_pc: int,
                   isfs_length: int) -> dict[str, bool]:
    end = isfs_pc + isfs_length
    direct = [
        branch_target(callback_pc + 4 * i, word)
        for i, word in enumerate(words)
    ]
    have_direct = any(t is not None and isfs_pc <= t < end for t in direct)
    exact_entry = any(t == isfs_pc for t in direct)
    prologue = any(t == ISFS_PROLOGUE for t in direct)
    return_from_lr = any(
        (word >> 26) == 19 and ((word >> 1) & 1023) == 16
        for word in words
    )
    indirect = any(
        (word >> 26) == 19 and ((word >> 1) & 1023) == 528
        for word in words
    )
    return {
        "direct_isfs": have_direct,
        "direct_entry": exact_entry,
        "direct_prologue": prologue,
        "lr_branch": return_from_lr,
        "ctr_branch": indirect,
    }

def private_audit(data: bytes) -> dict[str, bool]:
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise ValueError("private ELF digest mismatch")
    functions = parse_functions(data)
    cb_size = functions.get(CB, 0)
    isfs_size = functions.get(ISFS, 0)
    have_cb = bool(cb_size and cb_size <= 0x10000 and cb_size % 4 == 0)
    have_isfs = bool(isfs_size and isfs_size <= 0x10000 and isfs_size % 4 == 0)
    if not (have_cb and have_isfs):
        raise ValueError("expected callback/ISFS symbols absent or invalid")
    header = HEADER.unpack_from(data)
    # ELF32 header indices: [11] e_shentsize, [12] e_shnum,
    # [13] e_shstrndx. Do not mistake section-string index for count.
    shoff, shentsize, shnum = header[6], header[11], header[12]
    if shentsize != SECTION.size or shoff + shnum * SECTION.size > len(data):
        raise ValueError("private ELF section geometry changed")
    spans = []
    for i in range(shnum):
        _, kind, flags, addr, off, size, *_ = SECTION.unpack_from(
            data, shoff + i * SECTION.size
        )
        if not (flags & 4) or kind == 8:  # executable and file-backed
            continue
        if off <= len(data) and size <= len(data) - off:
            spans.append((addr, addr + size, off))
    owners = [
        (lo, hi, off) for lo, hi, off in spans
        if lo <= CB and CB + cb_size <= hi
    ]
    if len(owners) != 1:
        raise ValueError("callback does not belong to one executable ELF section")
    lo, _, off = owners[0]
    position = off + (CB - lo)
    words = [
        struct.unpack_from(">I", data, position + index * 4)[0]
        for index in range(cb_size // 4)
    ]
    evidence = classify_words(CB, words, ISFS, isfs_size)
    evidence.update({
        "digest": True,
        "callback": have_cb,
        "isfs": have_isfs,
        "executable": True,
        "separate": CB + cb_size <= ISFS,
        "same_section": any(lo <= ISFS and ISFS + isfs_size <= hi
                            for lo, hi, _ in owners),
        "text": TEXT_MIN <= CB < TEXT_MAX and TEXT_MIN <= ISFS < TEXT_MAX,
    })
    return evidence

def format_result(v: dict[str, bool]) -> str:
    ordered = (
        "digest", "callback", "isfs", "executable", "separate",
        "same_section", "text", "direct_isfs", "direct_entry",
        "direct_prologue", "lr_branch", "ctr_branch"
    )
    return "V243_ORIGINAL_BRANCH " + " ".join(
        f"{key}={int(bool(v[key]))}" for key in ordered
    )

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf", type=Path)
    a = p.parse_args()
    print(format_result(private_audit(a.owner_elf.read_bytes())))
