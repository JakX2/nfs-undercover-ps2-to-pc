#!/usr/bin/env python3
"""V53 fail-closed owner-original mask+EXI DOL geometry oracle."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_exi_poll_v52 import make as make_v52
from make_start_to_eximask_v53 import MASK,MASK_SIZE,EXI,OLD_STOP,STOP,START,verify_original
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word

def verify(actual:bytes,owner:Path)->None:
    prev=make_v52(owner)
    original_mask,original_exi=verify_original(owner.read_bytes())
    old_text,old_data=sections_of(prev)
    new_text,new_data=sections_of(actual)
    if (len(old_text)!=7 or len(new_text)!=7 or new_data!=old_data or
        word(actual,0xE0)!=START or actual[0xE0:0x100]!=prev[0xE0:0x100]):
        raise ValueError("V53 DOL header/data or entrypoint modified")
    mask_matches=0
    for i,((base,old_code),(new_base,new_code)) in enumerate(zip(old_text,new_text)):
        if base!=new_base:
            raise ValueError("V53 shifted inherited guest text segment base")
        expected=bytearray(old_code)
        if base<=MASK and MASK+MASK_SIZE<=base+len(expected):
            mask_matches+=1
            at=MASK-base
            if expected[at:at+MASK_SIZE]!=struct.pack(">I",NOP)*(MASK_SIZE//4):
                raise ValueError("V52 original mask destination not synthetic NOPs")
            expected[at:at+MASK_SIZE]=original_mask
        if i==6:
            if expected[EXI-base:OLD_STOP-base]!=original_exi[:OLD_STOP-EXI]:
                raise ValueError("V52 EXI prefix differs from owner original")
            if expected[OLD_STOP-base:]!=struct.pack(">II",SC,BLR):
                raise ValueError("V52 EXI synthetic boundary overwritten")
            expected[OLD_STOP-base:]=original_exi[OLD_STOP-EXI:]+struct.pack(">II",SC,BLR)
            if len(expected)!=STOP+8-base:
                raise ValueError("V53 EXI stop not aligned to section end")
        if new_code!=expected:
            raise ValueError("V53 modified unexpected translated or synthetic text")
    if mask_matches!=1:
        raise ValueError("V53 mask range matched incorrect number of segments")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_dol)
    print("PASS: V53 mask/EXI owner-original no-overwrite DOL geometry verified")
