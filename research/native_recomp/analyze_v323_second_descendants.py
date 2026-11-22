#!/usr/bin/env python3
"""V323: original Wii instruction coverage of the 64-word NAND helper's callees.

V317 proved these five generated native call edges exist, but AOT presence
alone does not prove that the reduced Wii fixture contains original code.
Compare exact SHA-authenticated DOL/ELF and the private V310 fixture, using
sized ELF entries or verified tails for interior branch targets. Report
counts and native mapping flags only, never instruction words or game C++.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

from audit_v292_nand_aot_reach import emitted,word_counts
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from resolve_v308_descendant_boundaries import resolve

TARGETS=(0x805195EC,0x8051AD38,0x80522294,0x80545100,0x8054514C)

def inspect(owner:bytes, elf:bytes, fixture:bytes, generated:str,
            *, dol_digest:str=ORIGINAL_SHA,
            elf_digest:str=ORIGINAL_SHA256,
            parser=parse_functions, reader=text_at)->list[str]:
    if (hashlib.sha256(owner).hexdigest()!=dol_digest or
        hashlib.sha256(elf).hexdigest()!=elf_digest):
        raise ValueError("authenticated_digest")
    if (not fixture or len(fixture)>20_000_000 or
        not generated or len(generated)>50_000_000):
        raise ValueError("private_geometry")
    sizes=parser(elf)
    original=missing=partial=unknown=emitted_count=dispatch_count=0
    rows=[]
    for pc in TARGETS:
        window=resolve(sizes,pc)
        if window.length:
            source=reader(owner,pc,window.length)
            if len(source)!=window.length:
                raise ValueError("original_span")
            try:
                before=reader(fixture,pc,window.length)
                present=int(len(before)==window.length)
            except (ValueError,IndexError):
                before=b""
                present=0
            counts=word_counts(source,before) if present else {
                "same":0,"nop":0,"blr":0,"other":0
            }
            authentic=int(bool(present and counts["same"]==window.length//4))
            original+=authentic
            missing+=int(not present)
            partial+=int(bool(present and not authentic))
        else:
            present=authentic=0
            counts={"same":0,"nop":0,"blr":0,"other":0}
            unknown+=1
        # AOT entries for interior targets may be synthesized separately
        # from the enclosing STT_FUNC. Audit the exact called address.
        entry=emitted(generated,pc)
        emitted_count+=entry["body"]
        dispatch_count+=entry["dispatch"]
        rows.append(
            f"V323_CALLEE pc={pc:08x} kind={window.kind} "
            f"base={window.entry:08x} offset={window.offset//4} "
            f"words={window.length//4} present={present} "
            f"same={counts['same']} nop={counts['nop']} "
            f"blr={counts['blr']} other={counts['other']} "
            f"original={authentic} body={entry['body']} "
            f"dispatch={entry['dispatch']}"
        )
    return [
        f"V323_SECOND_COVERAGE owner=1 targets={len(TARGETS)} "
        f"original={original} missing={missing} partial={partial} "
        f"unknown={unknown} body={emitted_count} dispatch={dispatch_count}"
    ]+rows

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("owner_elf",type=Path)
    p.add_argument("private_v310_dol",type=Path)
    p.add_argument("private_v310_generated_cpp",type=Path)
    a=p.parse_args()
    try:
        result=inspect(
            a.owner_dol.read_bytes(),a.owner_elf.read_bytes(),
            a.private_v310_dol.read_bytes(),
            a.private_v310_generated_cpp.read_text(encoding="utf-8",errors="replace")
        )
    except (OSError,ValueError,IndexError):
        print("V323_SECOND_AUDIT verified=0",file=sys.stderr)
        return 1
    print("\n".join(result))
    print("V323_SECOND_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
