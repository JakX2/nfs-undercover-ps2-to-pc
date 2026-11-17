#!/usr/bin/env python3
"""Fail-closed original PPC coverage, no-overwrite and SHA guards for V40."""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from make_start_to_cache_v39 import make as make_v39, STOP as PREVIOUS_STOP
from make_start_to_vectorcopy_v38 import OSINIT, word
from make_start_to_vectors_v40 import STOP
from make_osinit_execparams_v28 import text_at, SC, BLR

def verify(image:bytes,owner:Path)->None:
    previous=make_v39(owner) # inherits exact owner SHA, code/fixture assertions
    if len(image)!=len(previous) or image[:256]!=previous[:256]:
        raise ValueError("V40 private original DOL layout or length changed")
    off,guest,size=(word(image,k+4) for k in (0,0x48,0x90))
    if off<256 or guest!=OSINIT or STOP+8>guest+size or word(image,0xE0)!=0x8000403C:
        raise ValueError("V40 original __start / OSInit mapping changed")
    lo=off+PREVIOUS_STOP-guest
    hi=off+STOP+8-guest
    if image[:lo]!=previous[:lo] or image[hi:]!=previous[hi:]:
        raise ValueError("V40 changed previously verified Wii PPC or private oracle bytes")
    if image[lo:hi-8]!=text_at(owner.read_bytes(),PREVIOUS_STOP,STOP-PREVIOUS_STOP):
        raise ValueError("V40 genuine exception loopback differs from original DOL")
    if image[hi-8:hi]!=struct.pack(">II",SC,BLR):
        raise ValueError("V40 terminal test-only syscall/return guard mutated")

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("private_fixture",type=Path)
    ap.add_argument("owner_original_dol",type=Path)
    a=ap.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: V40 original Wii 15-vector instructions and no-overwrite geometry verified")
