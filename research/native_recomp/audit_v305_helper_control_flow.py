#!/usr/bin/env python3
"""V305: SHA-pinned static control flow of original Wii NAND helper 0x804F2064.

This is a read-only source audit. The original executable is never
recompiled, serialized, or included in repository files. Only bounded
addresses and instruction-class counts from the authenticated ELF leave CI.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys

from audit_v243_original_callback_branch import branch_target
from audit_v264_osinit_retry_elf import read_words
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions

FUNC = 0x804F2064
ORIGINAL_WORDS = 41

def analyze_words(words: list[int], pc: int = FUNC) -> list[str]:
    if pc != FUNC or len(words) != ORIGINAL_WORDS or any(
        not 0 <= w <= 0xffffffff for w in words
    ):
        raise ValueError("helper_geometry")
    direct: Counter[int] = Counter()
    cond = local = bclr = bcctr = conditional_calls = 0
    for i, word in enumerate(words):
        op = word >> 26
        xo = (word >> 1) & 1023
        link = bool(word & 1)
        here = pc + i*4
        if op == 16:
            cond += 1
            if link:
                conditional_calls += 1
                target = branch_target(here,word)
                if target is not None:
                    direct[target] += 1
        elif op == 18:
            target = branch_target(here,word)
            if target is None:
                raise ValueError("branch_decode")
            if link:
                direct[target] += 1
            elif pc <= target < pc+len(words)*4:
                local += 1
        elif op == 19 and xo == 16:
            bclr += 1
        elif op == 19 and xo == 528:
            bcctr += 1
    result = [
        f"V305_HELPER_FLOW original=1 pc={pc:08x} words={len(words)} "
        f"calls={sum(direct.values())} targets={len(direct)} "
        f"conditional_calls={conditional_calls} conditional_branches={cond} "
        f"local_jumps={local} bclr={bclr} bcctr={bcctr}"
    ]
    for rank, (target, n) in enumerate(sorted(
        direct.items(), key=lambda item: (-item[1],item[0])
    )[:12],1):
        result.append(
            f"V305_HELPER_CALLEE rank={rank} target={target:08x} calls={n}"
        )
    return result

def audit(data: bytes, expected_digest: str = ORIGINAL_SHA256,
          symbol_parser=parse_functions, word_reader=read_words) -> list[str]:
    if hashlib.sha256(data).hexdigest() != expected_digest:
        raise ValueError("original_sha")
    functions = symbol_parser(data)
    if functions.get(FUNC) != ORIGINAL_WORDS*4:
        raise ValueError("symbol_size")
    words = word_reader(data,FUNC,ORIGINAL_WORDS)
    return analyze_words(words)

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_private_elf",type=Path)
    args = p.parse_args()
    try:
        lines = audit(args.owner_private_elf.read_bytes())
    except (OSError,ValueError):
        print("V305_HELPER_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V305_HELPER_AUDIT verified=1")
    print("\n".join(lines))
    return 0

if __name__ == "__main__":
    sys.exit(main())
