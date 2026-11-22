#!/usr/bin/env python3
"""V310: exact private restoration of the first missing NAND descendant.

V308 owner audit proved the 64-word 0x80519BCC function is entirely NOP
in the private V302 reduced DOL. Require all 64 placeholders, authentic
owner DOL and ELF digests, exact ELF symbol extent, and reversible DOL
installation. Never emit original words, translated C++, or private files.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys

from extend_private_text import NOP, install
from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions
from restore_v293_private_nand import classify_span

TARGET=0x80519BCC
WORDS=64
SIZE=WORDS*4

def restore(owner:bytes, fixture:bytes, size:int=SIZE,
            reader=text_at)->tuple[bytes,str]:
    if not owner or not fixture or len(fixture)>20_000_000:
        raise ValueError("fixture_size")
    if size!=SIZE:
        raise ValueError("function_size")
    original=reader(owner,TARGET,SIZE)
    prior=reader(fixture,TARGET,SIZE)
    if len(original)!=SIZE or len(prior)!=SIZE:
        raise ValueError("function_span")
    same,nop=classify_span(original,prior)
    if (same,nop)!=(0,WORDS) or prior!=NOP*WORDS:
        raise ValueError("not_exact_nop_fixture")
    restored=install(fixture,[(TARGET,prior,original)])
    if reader(restored,TARGET,SIZE)!=original:
        raise ValueError("restoration_mismatch")
    inverse=install(restored,[(TARGET,original,prior)])
    if inverse!=fixture:
        raise ValueError("roundtrip")
    return restored,(
        f"V310_DESCENDANT_RESTORE owner=1 pc={TARGET:08x} "
        f"words={WORDS} same={same} nop={nop} roundtrip=1 candidate=1"
    )

def audit(owner:bytes, elf:bytes, fixture:bytes,
          *, dol_digest:str=ORIGINAL_SHA, elf_digest:str=ORIGINAL_SHA256,
          parser=parse_functions, reader=text_at)->tuple[bytes,str]:
    if (hashlib.sha256(owner).hexdigest()!=dol_digest or
        hashlib.sha256(elf).hexdigest()!=elf_digest):
        raise ValueError("authenticated_digest")
    functions=parser(elf)
    if functions.get(TARGET)!=SIZE:
        raise ValueError("function_size")
    return restore(owner,fixture,SIZE,reader)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("owner_elf",type=Path)
    p.add_argument("private_reduced_dol",type=Path)
    p.add_argument("private_restored_output",type=Path)
    a=p.parse_args()
    if a.private_restored_output.exists() or a.private_restored_output.is_symlink():
        print("V310_RESTORE_AUDIT verified=0",file=sys.stderr)
        return 1
    try:
        restored,row=audit(
            a.owner_dol.read_bytes(),a.owner_elf.read_bytes(),
            a.private_reduced_dol.read_bytes()
        )
        with a.private_restored_output.open("xb") as output:
            output.write(restored)
    except (OSError,ValueError):
        print("V310_RESTORE_AUDIT verified=0",file=sys.stderr)
        return 1
    print(row)
    print("V310_RESTORE_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
