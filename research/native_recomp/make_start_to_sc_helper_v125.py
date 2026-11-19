#!/usr/bin/env python3
"""Restore bounded original V125 SC helper text in the private Wii fixture only."""
import argparse
import hashlib
import struct
from pathlib import Path
from make_start_to_ipc_ack_v77 import make as previous
from make_start_to_irq_enable_v68 import replace
from make_osinit_execparams_v28 import ORIGINAL_SHA,NOP,text_at

ENTRY=0x8051E5BC
MAX_SPAN=0x200
MIN_SPAN=0x20
NOP_WORD=struct.pack(">I",NOP)

def extent(inherited:bytes)->int:
    count=0
    for offset in range(0,MAX_SPAN,4):
        try:
            word=text_at(inherited,ENTRY+offset,4)
        except ValueError:
            break
        if word!=NOP_WORD:
            break
        count+=4
    if count<MIN_SPAN:
        raise ValueError("V125 original helper has no verified NOP-only fixture range")
    return count

def authenticated_span(owner:Path,size:int)->bytes:
    original=owner.read_bytes()
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("V125 original Wii SHA-256 validation failed")
    code=text_at(original,ENTRY,size)
    if len(code)!=size or code[:4] in (NOP_WORD,b"\0\0\0\0"):
        raise ValueError("V125 authentic helper entry missing")
    return code

def make(owner:Path)->bytes:
    inherited=bytearray(previous(owner))
    size=extent(inherited)
    body=authenticated_span(owner,size)
    replace(inherited,ENTRY,NOP_WORD*(size//4),body)
    return bytes(inherited)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_owner",type=Path)
    p.add_argument("output_private_fixture",type=Path)
    a=p.parse_args()
    if a.output_private_fixture.exists() or a.output_private_fixture.is_symlink():
        p.error("refusing private fixture overwrite")
    with a.output_private_fixture.open("xb") as f:
        f.write(make(a.original_owner))
    print("PASS: V125 original SC helper restored in private fixture")
