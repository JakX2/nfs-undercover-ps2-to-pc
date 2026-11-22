#!/usr/bin/env python3
"""V301: owner-private authenticity and AOT mapping of first NAND service helper.

The SHA-pinned Wii DOL/ELF remain private. Inspect exactly one authenticated
0x804F2064 function and its call from 0x8051D20C. Only bounded word counts,
public addresses and emitted/dispatch booleans may leave owner CI.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions
from audit_v245_generated_callback import body_at
from audit_v292_nand_aot_reach import word_counts, emitted

TARGET = 0x804F2064
CALLER = 0x8051D20C

def analyze(original: bytes, elf: bytes, fixture: bytes, generated: str,
            *, dol_sha: str=ORIGINAL_SHA,
            elf_sha: str=ORIGINAL_SHA256,
            parser=parse_functions, reader=text_at) -> str:
    if (hashlib.sha256(original).hexdigest()!=dol_sha or
        hashlib.sha256(elf).hexdigest()!=elf_sha):
        raise ValueError("owner_sha")
    if (not fixture or len(fixture)>20_000_000 or not generated or
        len(generated)>50_000_000):
        raise ValueError("fixture_geometry")
    sizes=parser(elf)
    size=sizes.get(TARGET,0)
    if size < 4 or size > 32768 or size%4:
        raise ValueError("helper_size")
    source=reader(original,TARGET,size)
    if len(source)!=size:
        raise ValueError("original_geometry")
    try:
        reduction=reader(fixture,TARGET,size)
        present=int(len(reduction)==size)
    except (ValueError,IndexError):
        reduction=b""
        present=0
    if present:
        counts=word_counts(source,reduction)
    else:
        counts=dict(same=0,nop=0,blr=0,other=0)
    flags=emitted(generated,TARGET)
    caller=body_at(generated,CALLER).lower()
    target=f"0x{TARGET:08x}"
    linked=int(f"ctx.pc = {target}" in caller)
    unmapped=int(bool(re.search(
        r"ctx\.pc\s*=\s*"+target+
        r"\s*;\s*return\s*;\s*//\s*bl to unmapped target",caller)))
    direct=int(bool(re.search(
        r"ctx\.pc\s*=\s*"+target+r"\s*;[^{}]{0,120}\(ctx\)",caller)))
    return (
        f"V301_HELPER_AOT owner=1 elf=1 pc={TARGET:08x} "
        f"words={size//4} present={present} "
        f"same={counts['same']} nop={counts['nop']} "
        f"blr={counts['blr']} other={counts['other']} "
        f"body={flags['body']} dispatch={flags['dispatch']} "
        f"caller={linked} unmapped={unmapped} direct={direct}"
    )

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_dol",type=Path)
    p.add_argument("original_elf",type=Path)
    p.add_argument("private_aot_fixture",type=Path)
    p.add_argument("private_generated_cpp",type=Path)
    a=p.parse_args()
    try:
        result=analyze(
            a.original_dol.read_bytes(),
            a.original_elf.read_bytes(),
            a.private_aot_fixture.read_bytes(),
            a.private_generated_cpp.read_text(encoding="utf-8",errors="replace")
        )
    except (OSError,ValueError):
        print("V301_HELPER_AUDIT verified=0",file=sys.stderr)
        return 1
    print(result)
    print("V301_HELPER_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
