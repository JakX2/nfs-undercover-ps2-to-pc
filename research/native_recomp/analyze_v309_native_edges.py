#!/usr/bin/env python3
"""V309: verify native call edges to four authentic NAND-helper descendants.

An interior PowerPC target may have an enclosing AOT body but no
direct target dispatch. Inspect both explicitly. Authenticate original
Wii DOL/ELF and restored private helper; never emit original words,
private paths or generated game code.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

from analyze_v306_helper_descendants import TARGETS
from audit_v245_generated_callback import body_at
from audit_v292_nand_aot_reach import emitted
from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions
from resolve_v308_descendant_boundaries import resolve

HELPER=0x804F2064
HELPER_BYTES=41*4

def inspect(owner:bytes, elf:bytes, restored:bytes, generated:str,
            *, dol_digest:str=ORIGINAL_SHA,
            elf_digest:str=ORIGINAL_SHA256,
            parser=parse_functions, reader=text_at)->list[str]:
    if (hashlib.sha256(owner).hexdigest()!=dol_digest or
        hashlib.sha256(elf).hexdigest()!=elf_digest):
        raise ValueError("authenticated_digest")
    if (not restored or len(restored)>20_000_000 or
        not generated or len(generated)>50_000_000):
        raise ValueError("fixture_geometry")
    original=reader(owner,HELPER,HELPER_BYTES)
    private=reader(restored,HELPER,HELPER_BYTES)
    if original != private or len(original)!=HELPER_BYTES:
        raise ValueError("helper_original")
    helper=body_at(generated,HELPER)
    if not helper:
        raise ValueError("helper_not_emitted")
    funcs=parser(elf)
    rows=[]
    called=direct=unmapped=target_dispatch=parent_dispatch=0
    for pc in TARGETS:
        window=resolve(funcs,pc)
        token=f"0x{pc:08x}"
        # C++ translation edge, not an assertion of original call frequency.
        edge=re.search(r"ctx\.pc\s*=\s*"+token+r"\s*;",helper)
        callsite=int(edge is not None)
        indirect=int(bool(re.search(
            r"ctx\.pc\s*=\s*"+token+
            r"\s*;\s*return\s*;\s*//\s*bl to unmapped target",helper
        )))
        linked=int(bool(re.search(
            r"ctx\.pc\s*=\s*"+token+
            r"\s*;\s*[A-Za-z_][A-Za-z_0-9:]*\(ctx\)",helper
        )))
        target=emitted(generated,pc)
        parent=emitted(generated,window.entry or pc)
        called+=callsite
        direct+=linked
        unmapped+=indirect
        target_dispatch+=target["dispatch"]
        parent_dispatch+=parent["dispatch"]
        rows.append(
            f"V309_CALL_EDGE pc={pc:08x} kind={window.kind} "
            f"callsite={callsite} direct={linked} unmapped={indirect} "
            f"target_body={target['body']} "
            f"target_dispatch={target['dispatch']} "
            f"parent_body={parent['body']} "
            f"parent_dispatch={parent['dispatch']}"
        )
    return [
        f"V309_CALL_GRAPH original=1 targets={len(TARGETS)} "
        f"callsite={called} direct={direct} unmapped={unmapped} "
        f"target_dispatch={target_dispatch} parent_dispatch={parent_dispatch}"
    ]+rows

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("owner_elf",type=Path)
    p.add_argument("private_restored_dol",type=Path)
    p.add_argument("private_generated_cpp",type=Path)
    a=p.parse_args()
    try:
        lines=inspect(
            a.owner_dol.read_bytes(),
            a.owner_elf.read_bytes(),
            a.private_restored_dol.read_bytes(),
            a.private_generated_cpp.read_text(encoding="utf-8",errors="replace")
        )
    except (OSError,ValueError):
        print("V309_EDGE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("\n".join(lines))
    print("V309_EDGE_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
