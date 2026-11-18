#!/usr/bin/env python3
"""Exact original span, explicit boundary, and inherited-data oracle for V59."""
import argparse,struct
from pathlib import Path
from make_start_to_si_sampling_v58 import make as previous, STOP as PREV_STOP,REPEAT_STOP
from make_start_to_si_return_v59 import RANGES,GUARDS,DELAY_CALL
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word
def verify(actual,owner):
    old=previous(owner);raw=owner.read_bytes()
    if actual[:256]!=old[:256] or len(actual)!=len(old):
        raise ValueError("V59 changed inherited segment metadata")
    text,_=sections_of(old);base,body=text[5]
    expected=bytearray(old);off=word(old,5*4)
    for lo,hi in RANGES:
        for pc in range(lo,hi,4):
            inherited=SC if pc in (PREV_STOP,REPEAT_STOP) else BLR if pc in (PREV_STOP+4,REPEAT_STOP+4) else NOP
            if word(body,pc-base)!=inherited:
                raise ValueError("V59 overwrote prior genuine PPC")
            at=off+pc-base
            expected[at:at+4]=struct.pack(">I",SC) if pc==DELAY_CALL else text_at(raw,pc,4)
    for pc in GUARDS:
        if body[pc-base:pc-base+8]!=struct.pack(">II",NOP,NOP):
            raise ValueError("V59 callback boundary changed prior original")
        at=off+pc-base;expected[at:at+8]=struct.pack(">II",SC,BLR)
    if expected!=actual:raise ValueError("V59 owner original/guard comparison differs")
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture",type=Path);p.add_argument("owner",type=Path)
    a=p.parse_args();verify(a.fixture.read_bytes(),a.owner)
    print("PASS: V59 exact original SI discovery, transfer and return ranges")
