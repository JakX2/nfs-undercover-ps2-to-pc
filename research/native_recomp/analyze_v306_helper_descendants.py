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
from resolve_v308_descendant_boundaries import resolve

TARGETS=(0x80519BCC,0x8051AD38,0x80545104,0x80545150)
KNOWN_ERRORS={
    'authenticated_digest','fixture_geometry','function_size',
    'original_span','cpp_geometry','span_geometry','invalid_target'
}
def classify_error(exc:Exception)->str:
    if isinstance(exc,OSError):return 'input_io'
    msg=str(exc)
    return msg if msg in KNOWN_ERRORS else 'other'

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
    exact=interior=translated=dispatched=missing=partial=unknown=0
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
            counts=(word_counts(source,before) if present else
                    dict(same=0,nop=0,blr=0,other=0))
        else:
            present=0
            counts=dict(same=0,nop=0,blr=0,other=0)
            unknown+=1
        # An interior BL target does not create a new ELF function.
        # Inspect the actual enclosing entry for the native dispatch.
        entry=emitted(generated,window.entry or pc)
        authentic=int(bool(
            window.length and present and
            counts["same"]==window.length//4
        ))
        exact+=int(window.kind=="exact" and authentic)
        interior+=int(window.kind=="interior" and authentic)
        translated+=entry["body"]
        dispatched+=entry["dispatch"]
        missing+=int(bool(window.length and not present))
        partial+=int(bool(window.length and present and not authentic))
        rows.append(
            f"V306_DESCENDANT pc={pc:08x} kind={window.kind} "
            f"base={window.entry:08x} offset={window.offset//4} "
            f"words={window.length//4} present={present} "
            f"same={counts['same']} nop={counts['nop']} "
            f"blr={counts['blr']} other={counts['other']} "
            f"body={entry['body']} dispatch={entry['dispatch']}"
        )
    return [
        f"V306_COVERAGE owner=1 targets={len(TARGETS)} exact={exact} "
        f"interior={interior} emitted={translated} dispatch={dispatched} "
        f"missing={missing} partial={partial} unknown={unknown}"
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
    except (OSError,ValueError,IndexError) as exc:
        print('V306_COVERAGE_ERROR reason='+classify_error(exc),file=sys.stderr)
        print("V306_COVERAGE_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V306_COVERAGE_AUDIT verified=1")
    print("\n".join(rows))
    return 0

if __name__=="__main__":
    sys.exit(main())
