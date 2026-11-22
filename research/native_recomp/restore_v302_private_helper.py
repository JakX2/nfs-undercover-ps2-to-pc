#!/usr/bin/env python3
"""V302: owner-only restoration of original Wii NAND nested helper 0x804F2064.

Restore precisely its SHA-pinned PowerPC body to a separately written
private DOL. Existing source must be exact original bytes or NOP-only
placeholders; an absent span can be extended only through the existing
bounded, section-preserving private text installer. Never publish original
words, translated C++, private paths or assets.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
import sys

from extend_private_text import NOP, install, unpack
from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions
from restore_v293_private_nand import classify_span

TARGET=0x804F2064
MAX_FUNC=8192

def restore(original:bytes,fixture:bytes,size:int,reader=text_at)->tuple[bytes,str]:
    if not original or not fixture or len(fixture)>20_000_000:
        raise ValueError("fixture_geometry")
    if size<4 or size>MAX_FUNC or size%4:
        raise ValueError("helper_size")
    authentic=reader(original,TARGET,size)
    if len(authentic)!=size:
        raise ValueError("source_span")
    present=0
    try:
        prior=reader(fixture,TARGET,size)
        present=int(len(prior)==size)
    except (ValueError,IndexError,struct.error):
        prior=b""
    if present:
        same,nop=classify_span(authentic,prior)
        if not nop:
            raise ValueError("helper_already_original")
        expected=prior
    else:
        # This is an expected absence, NOT permission to overwrite a
        # non-NOP prefix. install() checks the complete proposed span.
        same=nop=0
        expected=NOP*(size//4)
    restored=install(fixture,[(TARGET,expected,authentic)])
    if reader(restored,TARGET,size)!=authentic:
        raise ValueError("candidate_mismatch")
    before=unpack(fixture)
    after=unpack(restored)
    if len(before)!=len(after):
        raise ValueError("section_count")
    extended=0
    for a,b in zip(before,after):
        if a[:3]!=b[:3] or len(b[3])<len(a[3]):
            raise ValueError("section_geometry")
        if len(b[3])>len(a[3]):
            extended+=1
    if restored==fixture:
        raise ValueError("no_restoration")
    return restored,(
        f"V302_HELPER_RESTORE owner=1 pc={TARGET:08x} "
        f"words={size//4} present={present} same={same} nop={nop} "
        f"extended={int(extended>0)} protected=1 candidate=1"
    )

def audit(original:bytes,elf:bytes,fixture:bytes,
          dol_sha:str=ORIGINAL_SHA,elf_sha:str=ORIGINAL_SHA256,
          parser=parse_functions,reader=text_at)->tuple[bytes,str]:
    if (hashlib.sha256(original).hexdigest()!=dol_sha or
        hashlib.sha256(elf).hexdigest()!=elf_sha):
        raise ValueError("authenticated_digest")
    sizes=parser(elf)
    return restore(original,fixture,sizes.get(TARGET,0),reader)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_dol",type=Path)
    p.add_argument("owner_elf",type=Path)
    p.add_argument("reduced_private_dol",type=Path)
    p.add_argument("restored_private_output",type=Path)
    a=p.parse_args()
    if a.restored_private_output.exists() or a.restored_private_output.is_symlink():
        print("V302_RESTORE_AUDIT verified=0",file=sys.stderr)
        return 1
    try:
        data,row=audit(
            a.owner_dol.read_bytes(),a.owner_elf.read_bytes(),
            a.reduced_private_dol.read_bytes()
        )
        with a.restored_private_output.open("xb") as dst:
            dst.write(data)
    except (OSError,ValueError):
        print("V302_RESTORE_AUDIT verified=0",file=sys.stderr)
        return 1
    print(row)
    print("V302_RESTORE_AUDIT verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
