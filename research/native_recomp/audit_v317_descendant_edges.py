#!/usr/bin/env python3
"""V317: authenticated AOT call-edge census for the restored 64-word NAND helper.

The complete original Wii game and generated native C++ stay on the private
owner runner. Report only the five original V312 call targets, ELF boundary
kind, native body/dispatch flags, and translated call-edge shapes. Never
alter, print, or upload executable data.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

from audit_v245_generated_callback import body_at
from audit_v292_nand_aot_reach import emitted
from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions
from resolve_v308_descendant_boundaries import resolve

HELPER = 0x80519BCC
HELPER_SIZE = 64 * 4
TARGETS = (0x805195EC, 0x8051AD38, 0x80522294, 0x80545100, 0x8054514C)

def inspect(owner: bytes, elf: bytes, candidate: bytes, generated: str,
            dol_digest: str=ORIGINAL_SHA, elf_digest: str=ORIGINAL_SHA256,
            symbol_parser=parse_functions, reader=text_at) -> list[str]:
    if (hashlib.sha256(owner).hexdigest() != dol_digest or
        hashlib.sha256(elf).hexdigest() != elf_digest):
        raise ValueError("authenticated_digest")
    if not generated or len(generated)>50_000_000 or not candidate or len(candidate)>20_000_000:
        raise ValueError("private_geometry")
    src=reader(owner,HELPER,HELPER_SIZE)
    original=reader(candidate,HELPER,HELPER_SIZE)
    if len(src)!=HELPER_SIZE or original!=src:
        raise ValueError("authentic_helper")
    body=body_at(generated,HELPER)
    if not body:
        raise ValueError("missing_body")
    symbols=symbol_parser(elf)
    edges=direct=unmapped=dispatch=0
    rows=[]
    for pc in TARGETS:
        geom=resolve(symbols,pc)
        token=f"0x{pc:08x}"
        has_edge=int(bool(re.search(r"ctx\.pc\s*=\s*"+token+r"\s*;",body)))
        has_unmapped=int(bool(re.search(
            r"ctx\.pc\s*=\s*"+token+
            r"\s*;\s*return\s*;\s*//\s*bl to unmapped target",body
        )))
        has_direct=int(bool(re.search(
            r"ctx\.pc\s*=\s*"+token+
            r"\s*;\s*[A-Za-z_][A-Za-z_0-9:]*\(ctx\)",body
        )))
        flags=emitted(generated,pc)
        edges+=has_edge
        direct+=has_direct
        unmapped+=has_unmapped
        dispatch+=flags["dispatch"]
        rows.append(
            f"V317_HELPER_EDGE pc={pc:08x} kind={geom.kind} "
            f"original=1 site={has_edge} direct={has_direct} "
            f"unmapped={has_unmapped} body={flags['body']} dispatch={flags['dispatch']}"
        )
    return [
        f"V317_HELPER_EDGES owner=1 pc={HELPER:08x} targets={len(TARGETS)} "
        f"site={edges} direct={direct} unmapped={unmapped} dispatch={dispatch}"
    ]+rows

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("owner_elf",type=Path)
    p.add_argument("private_v310_dol",type=Path)
    p.add_argument("private_v310_generated_cpp",type=Path)
    a=p.parse_args()
    try:
        rows=inspect(
            a.owner_dol.read_bytes(),a.owner_elf.read_bytes(),
            a.private_v310_dol.read_bytes(),
            a.private_v310_generated_cpp.read_text(encoding="utf-8",errors="replace")
        )
    except (OSError,ValueError):
        print("V317_EDGE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("\n".join(rows))
    print("V317_EDGE_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
