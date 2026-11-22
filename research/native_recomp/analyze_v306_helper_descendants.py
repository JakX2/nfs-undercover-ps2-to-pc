#!/usr/bin/env python3
"""V306: authenticated AOT coverage census for 0x804F2064's four callees.

Read only the SHA-pinned owner DOL/ELF, private V302 fixture and generated
native C++ within owner CI. Output bounded word counts and dispatch flags,
never original instruction bytes or generated game code.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys

from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions
from audit_v292_nand_aot_reach import word_counts, emitted

TARGETS=(0x80519BCC,0x8051AD38,0x80545104,0x80545150)

def inspect(owner: bytes, elf: bytes, fixture: bytes, generated: str,
            dol_digest: str=ORIGINAL_SHA,
            elf_digest: str=ORIGINAL_SHA256,
            parser=parse_functions,
            reader=text_at) -> list[str]:
    if hashlib.sha256(owner).hexdigest()!=dol_digest or (
        hashlib.sha256(elf).hexdigest()!=elf_digest):
        raise ValueError("authenticated_digest")
    if (not fixture or len(fixture)>20_000_000 or not generated
        or len(generated)>50_000_000):
        raise ValueError("fixture_geometry")
    sizes=parser(elf)
    rows=[]
    exact=translated=dispatched=missing=partial=0
    for pc in TARGETS:
        size=sizes.get(pc,0)
        if size<4 or size>32768 or size%4:
            raise ValueError("function_size")
        source=reader(owner,pc,size)
        if len(source)!=size:
            raise ValueError("original_span")
        try:
            before=reader(fixture,pc,size)
            present=int(len(before)==size)
        except (ValueError,IndexError):
            before=b""
            present=0
        counts=(word_counts(source,before) if present else
                dict(same=0,nop=0,blr=0,other=0))
        entry=emitted(generated,pc)
        authentic=int(bool(present and counts["same"]==size//4))
        exact+=authentic
        translated+=entry["body"]
        dispatched+=entry["dispatch"]
        missing+=int(not present)
        partial+=int(bool(present and not authentic))
        rows.append(
            f"V306_DESCENDANT pc={pc:08x} words={size//4} "
            f"present={present} same={counts['same']} nop={counts['nop']} "
            f"blr={counts['blr']} other={counts['other']} "
            f"body={entry['body']} dispatch={entry['dispatch']}"
        )
    return [
        f"V306_COVERAGE owner=1 targets={len(TARGETS)} exact={exact} "
        f"emitted={translated} dispatch={dispatched} "
        f"missing={missing} partial={partial}"
    ]+rows

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("owner_elf",type=Path)
    p.add_argument("private_restored_dol",type=Path)
    p.add_argument("private_generated_cpp",type=Path)
    a=p.parse_args()
    try:
        rows=inspect(
            a.owner_dol.read_bytes(),a.owner_elf.read_bytes(),
            a.private_restored_dol.read_bytes(),
            a.private_generated_cpp.read_text(encoding="utf-8",errors="replace")
        )
    except (OSError,ValueError):
        print("V306_COVERAGE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V306_COVERAGE_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
