#!/usr/bin/env python3
"""V276: original Wii source values of +0x188 field stores in SC writers.

Verify the same register base is used by the four field-to-SYSCONF
loads and the candidate local field stores. Classify a store's
low-byte source using conservative local straight-line PPC analysis.
Do not claim object alias across functions, execution of stores, or
actual SYSCONF state transition.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys
from audit_v264_osinit_retry_elf import read_words
from audit_v275_sc_field_xref import SC_WRITERS,FIELD,field_access,input_edges
from audit_v273_sc_provenance import resolve
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

def examine(owner:int,words:list[int])->list[str]:
    if owner not in SC_WRITERS or not 16<=len(words)<=8192:
        raise ValueError("geometry")
    edges=input_edges(owner,words)
    if len(edges)!=2:raise ValueError("input_edges")
    bases={ra for _,_,ra,_ in edges}
    if len(bases)!=1:raise ValueError("input_base_mismatch")
    base=next(iter(bases))
    entries=[]
    for i,word in enumerate(words):
        k=field_access(word)
        if not k.startswith("write"):continue
        rs=(word>>21)&31
        ra=(word>>16)&31
        src_kind,value=resolve(words,i,rs)
        source=(f"byte{value}" if src_kind=="const" and value in (0,1,2,3)
                else "otherconst" if src_kind=="const"
                else src_kind)
        entries.append(
            f"V276_LOCAL_WRITE owner={owner:08x} offset={i*4} "
            f"width={k.removeprefix('write_')} base_reg={ra} "
            f"same_base={int(ra==base)} source_reg={rs} source={source}")
    return [f"V276_FIELD_BASE owner={owner:08x} base_reg={base} "
            f"loads={len(edges)} writes={len(entries)}"]+entries


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    functions=parse_functions(data)
    if len(functions)<25000:raise ValueError("symbols")
    rows=[]
    for owner in SC_WRITERS:
        n=functions.get(owner,0)
        if n<32 or n>32768 or n%4:raise ValueError("function_bounds")
        rec=examine(owner,read_words(data,owner,n//4))
        if len(rec)!={0x80530ba0:3,0x80530dbc:2}[owner]:
            raise ValueError("field_writes")
        rows.extend(rec)
    return ["V276_FIELD_AUDIT_SUMMARY owners=2 loads=4 stores=3"]+rows


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: out=audit(a.owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V276_FIELD_VALUES verified=0",file=sys.stderr)
        return 1
    print("V276_FIELD_VALUES verified=1")
    print("\n".join(out))
    return 0

if __name__=="__main__":
    sys.exit(main())
