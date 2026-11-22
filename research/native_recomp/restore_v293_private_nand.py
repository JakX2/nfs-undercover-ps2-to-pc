#!/usr/bin/env python3
"""V293 private-only original NAND body restoration feasibility.

Restore four authentic Wii NAND/SC function spans from SHA-pinned owner DOL,
using exact symbol sizes from a second SHA-pinned original ELF. The
reduced AOT fixture must contain only NOP placeholders or exact original
words. Every other instruction and DOL section must round-trip unchanged.
No game bytes or generated C++ are emitted to public CI or repository.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
import sys
from extend_private_text import install,NOP
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

TARGETS=(0x8052fa60,0x8051d20c,0x8051e150,0x8052fca4)
MAX_FUNC=8192
MAX_TOTAL=16384

def classify_span(original:bytes,current:bytes)->tuple[int,int]:
    if len(original)!=len(current) or not original or len(original)%4:
        raise ValueError("span_geometry")
    same=nop=0
    for i in range(0,len(original),4):
        a=original[i:i+4]
        b=current[i:i+4]
        if a==b:same+=1
        elif b==NOP:nop+=1
        else:raise ValueError("foreign_fixture_word")
    return same,nop

def restore(original:bytes,fixture:bytes,functions:dict[int,int],
            reader=text_at)->tuple[bytes,list[str]]:
    if not original or not fixture or len(fixture)>20000000:
        raise ValueError("fixture_size")
    sizes=[]
    patches=[]
    total=0
    changed=0
    for pc in TARGETS:
        size=functions.get(pc,0)
        if size<16 or size>MAX_FUNC or size&3:
            raise ValueError("function_size")
        total+=size
        if total>MAX_TOTAL:raise ValueError("function_total")
        try:
            before=reader(fixture,pc,size)
            authentic=reader(original,pc,size)
        except (ValueError,IndexError,struct.error) as exc:
            raise ValueError("missing_function_span") from exc
        same,nop=classify_span(authentic,before)
        if nop==0 or same+nop!=size//4:
            raise ValueError("fixture_not_placeholder")
        changed+=nop
        patches.append((pc,before,authentic))
        sizes.append((pc,size//4,same,nop))
    candidate=install(fixture,patches)
    for pc,before,authentic in patches:
        if reader(candidate,pc,len(authentic))!=authentic:
            raise ValueError("candidate_mismatch")
    inverse=install(candidate,[(pc,authentic,before)
                               for pc,before,authentic in patches])
    if inverse!=fixture:raise ValueError("roundtrip")
    lines=[
        f"V293_NAND_RESTORE owner=1 funcs={len(sizes)} "
        f"changed={changed} total_words={total//4} roundtrip=1 candidate=1"
    ]
    for pc,words,same,nop in sizes:
        lines.append(
            f"V293_RESTORED pc={pc:08x} words={words} "
            f"already={same} nop={nop} foreign=0")
    return candidate,lines

def audit(original:bytes,elf:bytes,fixture:bytes,
          original_digest:str=ORIGINAL_SHA,
          elf_digest:str=ORIGINAL_SHA256,
          symbol_parser=parse_functions,
          reader=text_at)->tuple[bytes,list[str]]:
    if hashlib.sha256(original).hexdigest()!=original_digest or (
        hashlib.sha256(elf).hexdigest()!=elf_digest):
        raise ValueError("authenticated_digest")
    functions=symbol_parser(elf)
    if len(functions)<len(TARGETS):raise ValueError("symbols")
    return restore(original,fixture,functions,reader)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("owner_elf",type=Path)
    p.add_argument("private_reduced_fixture",type=Path)
    p.add_argument("private_candidate_output",type=Path)
    a=p.parse_args()
    if a.private_candidate_output.exists() or a.private_candidate_output.is_symlink():
        print("V293_RESTORE_AUDIT verified=0",file=sys.stderr)
        return 1
    try:
        candidate,rows=audit(a.owner_dol.read_bytes(),
                             a.owner_elf.read_bytes(),
                             a.private_reduced_fixture.read_bytes())
        with a.private_candidate_output.open("xb") as stream:
            stream.write(candidate)
    except (OSError,ValueError):
        print("V293_RESTORE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V293_RESTORE_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
